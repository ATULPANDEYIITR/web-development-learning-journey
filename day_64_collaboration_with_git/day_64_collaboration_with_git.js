"use strict";

/*
 * Event-driven repository governance simulator.
 *
 * Run with Node.js 18 or later:
 *     node git-collaboration.js
 *
 * It models branch snapshots, Pull Request lifecycle events, review history,
 * status checks, conversation threads, and policy-based merge evaluation.
 * It does not create real Git objects or interact with a remote hosting API.
 */

const { EventEmitter } = require("node:events");
const { createHash } = require("node:crypto");

class WorkflowError extends Error {
    constructor(message, code = "WORKFLOW_ERROR") {
        super(message);
        this.name = "WorkflowError";
        this.code = code;
    }
}

const PRState = Object.freeze({
    DRAFT: "draft",
    OPEN: "open",
    CLOSED: "closed",
    MERGED: "merged"
});

const ReviewState = Object.freeze({
    APPROVED: "approved",
    CHANGES_REQUESTED: "changes_requested",
    COMMENTED: "commented",
    DISMISSED: "dismissed"
});

const CheckState = Object.freeze({
    PENDING: "pending",
    PASSED: "passed",
    FAILED: "failed",
    CANCELLED: "cancelled"
});

const MergeStrategy = Object.freeze({
    MERGE_COMMIT: "merge_commit",
    SQUASH: "squash",
    REBASE: "rebase"
});

function validateName(value, label) {
    if (typeof value !== "string" || value.trim() === "") {
        throw new TypeError(`${label} must be a non-empty string.`);
    }
}

function validatePath(path) {
    validateName(path, "Repository path");
    if (
        path.startsWith("/") ||
        path.includes("\\") ||
        path.split("/").some(part => part === "" || part === "." || part === "..")
    ) {
        throw new WorkflowError(`Unsafe repository path: ${path}`, "INVALID_PATH");
    }
}

function hashCommit(parents, message, tree) {
    const sortedTree = Object.fromEntries(
        [...tree.entries()].sort(([a], [b]) => a.localeCompare(b))
    );
    const payload = JSON.stringify({
        parents,
        message,
        tree: sortedTree
    });

    return createHash("sha256").update(payload).digest("hex");
}

class Branch {
    constructor(name, head, tree, protectedBranch = false) {
        this.name = name;
        this.head = head;
        this.tree = new Map(tree);
        this.protected = protectedBranch;
        this.deleted = false;
    }
}

class PullRequest {
    constructor({
        number,
        author,
        source,
        target,
        baseHead,
        sourceHead,
        draft
    }) {
        this.number = number;
        this.author = author;
        this.source = source;
        this.target = target;
        this.baseHeadAtOpen = baseHead;
        this.baseHeadAtSync = baseHead;
        this.sourceHead = sourceHead;
        this.state = draft ? PRState.DRAFT : PRState.OPEN;
        this.draft = draft;

        this.reviews = [];
        this.latestReviewByUser = new Map();
        this.checks = new Map();
        this.threads = new Map();
        this.mergeResult = null;
    }
}

class RepositoryGovernance extends EventEmitter {
    constructor(name, initialTree, policy) {
        super();

        validateName(name, "Repository name");
        if (!(initialTree instanceof Map)) {
            throw new TypeError("Initial tree must be a Map.");
        }

        this.name = name;
        this.branches = new Map();
        this.pullRequests = new Map();
        this.reviewers = new Map();
        this.commits = new Map();
        this.policy = this.normalizePolicy(policy);
        this.sequence = 0;
        this.eventLog = [];

        for (const [path, content] of initialTree.entries()) {
            validatePath(path);
            if (typeof content !== "string") {
                throw new TypeError(`File content for ${path} must be a string.`);
            }
        }

        const initial = this.createCommit([], "Initial repository state", initialTree);
        this.branches.set(
            "main",
            new Branch("main", initial.sha, initial.tree, true)
        );

        this.on("repository-event", event => {
            this.eventLog.push(Object.freeze({ ...event }));
        });
    }

    normalizePolicy(policy = {}) {
        const normalized = {
            minimumApprovals: policy.minimumApprovals ?? 2,
            requiredChecks: new Set(policy.requiredChecks ?? ["unit-tests", "security-scan"]),
            requireConversationResolution: policy.requireConversationResolution ?? true,
            requireLinearHistory: policy.requireLinearHistory ?? true,
            requirePullRequest: policy.requirePullRequest ?? true,
            allowMergeCommit: policy.allowMergeCommit ?? false,
            allowSquash: policy.allowSquash ?? true,
            allowRebase: policy.allowRebase ?? true,
            allowDirectPush: policy.allowDirectPush ?? false,
            allowForcePush: policy.allowForcePush ?? false,
            prohibitBranchDeletion: policy.prohibitBranchDeletion ?? true,
            allowAdminBypass: policy.allowAdminBypass ?? false
        };

        if (!Number.isInteger(normalized.minimumApprovals) || normalized.minimumApprovals < 0) {
            throw new TypeError("minimumApprovals must be a non-negative integer.");
        }

        for (const check of normalized.requiredChecks) {
            validateName(check, "Required check");
        }

        return Object.freeze(normalized);
    }

    emitDomainEvent(type, payload = {}) {
        const event = {
            id: ++this.sequence,
            type,
            timestamp: new Date().toISOString(),
            repository: this.name,
            ...payload
        };
        this.emit("repository-event", event);
    }

    createCommit(parents, message, tree) {
        validateName(message, "Commit message");

        const copiedTree = new Map(tree);
        const sha = hashCommit(parents, message, copiedTree);
        const commit = Object.freeze({
            sha,
            parents: Object.freeze([...parents]),
            message,
            tree: copiedTree
        });

        this.commits.set(sha, commit);
        return commit;
    }

    requireBranch(name) {
        const branch = this.branches.get(name);
        if (!branch || branch.deleted) {
            throw new WorkflowError(`Branch '${name}' does not exist.`, "BRANCH_NOT_FOUND");
        }
        return branch;
    }

    registerReviewer(username, attributes = {}) {
        validateName(username, "Reviewer username");

        this.reviewers.set(username, Object.freeze({
            username,
            active: attributes.active ?? true,
            canReview: attributes.canReview ?? true,
            administrator: attributes.administrator ?? false,
            roles: new Set(attributes.roles ?? ["developer"])
        }));
    }

    createBranch(name, from = "main") {
        validateName(name, "Branch name");

        if (this.branches.has(name)) {
            throw new WorkflowError(`Branch '${name}' already exists.`, "DUPLICATE_BRANCH");
        }

        const source = this.requireBranch(from);
        this.branches.set(name, new Branch(name, source.head, source.tree));
        this.emitDomainEvent("branch.created", { branch: name, base: from });
    }

    commitToBranch(branchName, author, message, changes) {
        const branch = this.requireBranch(branchName);
        validateName(author, "Commit author");
        validateName(message, "Commit message");

        if (branch.protected && (
            this.policy.requirePullRequest ||
            !this.policy.allowDirectPush
        )) {
            throw new WorkflowError(
                `Direct push to protected branch '${branchName}' is prohibited.`,
                "DIRECT_PUSH_BLOCKED"
            );
        }

        if (!(changes instanceof Map) || changes.size === 0) {
            throw new TypeError("changes must be a non-empty Map.");
        }

        const updatedTree = new Map(branch.tree);
        for (const [path, content] of changes.entries()) {
            validatePath(path);
            if (content === null) {
                updatedTree.delete(path);
            } else if (typeof content === "string") {
                updatedTree.set(path, content);
            } else {
                throw new TypeError(`Invalid content for '${path}'.`);
            }
        }

        const commit = this.createCommit([branch.head], message, updatedTree);
        branch.head = commit.sha;
        branch.tree = new Map(commit.tree);

        for (const pr of this.pullRequests.values()) {
            if (
                pr.source === branchName &&
                [PRState.OPEN, PRState.DRAFT].includes(pr.state)
            ) {
                pr.sourceHead = commit.sha;
                this.emitDomainEvent("pull_request.source_updated", {
                    pullRequest: pr.number,
                    newHead: commit.sha,
                    previousReviewsNowStale: true
                });
            }
        }

        this.emitDomainEvent("commit.created", {
            branch: branchName,
            author,
            sha: commit.sha
        });

        return commit.sha;
    }

    openPullRequest({
        number,
        author,
        source,
        target = "main",
        draft = true
    }) {
        if (!Number.isInteger(number) || number <= 0 || this.pullRequests.has(number)) {
            throw new WorkflowError("Pull Request number must be positive and unique.");
        }

        validateName(author, "Pull Request author");
        const sourceBranch = this.requireBranch(source);
        const targetBranch = this.requireBranch(target);

        if (source === target) {
            throw new WorkflowError("Source and target branches must differ.");
        }

        const pr = new PullRequest({
            number,
            author,
            source,
            target,
            baseHead: targetBranch.head,
            sourceHead: sourceBranch.head,
            draft
        });

        this.pullRequests.set(number, pr);
        this.emitDomainEvent("pull_request.opened", {
            pullRequest: number,
            author,
            source,
            target,
            draft
        });
        return pr;
    }

    requirePullRequest(number) {
        const pr = this.pullRequests.get(number);
        if (!pr) {
            throw new WorkflowError(`Pull Request #${number} does not exist.`);
        }
        return pr;
    }

    markReady(number) {
        const pr = this.requirePullRequest(number);
        if (pr.state !== PRState.DRAFT) {
            throw new WorkflowError("Only a draft Pull Request can become ready.");
        }

        pr.state = PRState.OPEN;
        pr.draft = false;
        this.emitDomainEvent("pull_request.ready", { pullRequest: number });
    }

    closePullRequest(number) {
        const pr = this.requirePullRequest(number);
        if (![PRState.DRAFT, PRState.OPEN].includes(pr.state)) {
            throw new WorkflowError("Only an open or draft Pull Request can be closed.");
        }

        pr.state = PRState.CLOSED;
        this.emitDomainEvent("pull_request.closed", { pullRequest: number });
    }

    reopenPullRequest(number) {
        const pr = this.requirePullRequest(number);
        if (pr.state !== PRState.CLOSED) {
            throw new WorkflowError("Only a closed Pull Request can be reopened.");
        }

        pr.state = PRState.OPEN;
        pr.draft = false;
        this.emitDomainEvent("pull_request.reopened", { pullRequest: number });
    }

    synchronizeBase(number) {
        const pr = this.requirePullRequest(number);
        if (![PRState.OPEN, PRState.DRAFT].includes(pr.state)) {
            throw new WorkflowError("Only an active Pull Request can be synchronized.");
        }

        const source = this.requireBranch(pr.source);
        const target = this.requireBranch(pr.target);
        const base = this.commits.get(pr.baseHeadAtSync).tree;
        const mergedTree = new Map(source.tree);
        const conflicts = [];

        const paths = new Set([
            ...base.keys(),
            ...source.tree.keys(),
            ...target.tree.keys()
        ]);

        for (const path of paths) {
            const baseValue = base.has(path) ? base.get(path) : undefined;
            const sourceValue = source.tree.has(path) ? source.tree.get(path) : undefined;
            const targetValue = target.tree.has(path) ? target.tree.get(path) : undefined;

            const sourceChanged = sourceValue !== baseValue;
            const targetChanged = targetValue !== baseValue;

            if (sourceChanged && targetChanged && sourceValue !== targetValue) {
                conflicts.push(path);
            } else if (targetChanged) {
                if (targetValue === undefined) {
                    mergedTree.delete(path);
                } else {
                    mergedTree.set(path, targetValue);
                }
            }
        }

        if (conflicts.length > 0) {
            this.emitDomainEvent("pull_request.sync_conflict", {
                pullRequest: number,
                paths: [...conflicts].sort()
            });
            return { synchronized: false, conflicts: [...conflicts].sort() };
        }

        const syncCommit = this.createCommit(
            [source.head, target.head],
            `Synchronize ${pr.target} into ${pr.source}`,
            mergedTree
        );

        source.head = syncCommit.sha;
        source.tree = new Map(syncCommit.tree);
        pr.sourceHead = syncCommit.sha;
        pr.baseHeadAtSync = target.head;

        this.emitDomainEvent("pull_request.base_synchronized", {
            pullRequest: number,
            sourceHead: syncCommit.sha,
            targetHead: target.head,
            reviewsNowStale: true
        });

        return { synchronized: true, conflicts: [] };
    }

    submitReview(number, reviewerName, state) {
        const pr = this.requirePullRequest(number);
        const reviewer = this.reviewers.get(reviewerName);

        if (!reviewer || !reviewer.active || !reviewer.canReview) {
            throw new WorkflowError(`${reviewerName} is not eligible to review.`);
        }
        if (reviewerName === pr.author) {
            throw new WorkflowError("Authors cannot review their own Pull Requests.");
        }
        if (pr.state !== PRState.OPEN || pr.draft) {
            throw new WorkflowError("Reviews require an open, non-draft Pull Request.");
        }
        if (!Object.values(ReviewState).includes(state) || state === ReviewState.DISMISSED) {
            throw new WorkflowError("Use dismissReview for dismissal events.");
        }

        const review = Object.freeze({
            reviewer: reviewerName,
            state,
            reviewedHead: pr.sourceHead,
            sequence: ++this.sequence,
            submittedAt: new Date().toISOString()
        });

        pr.reviews.push(review);
        pr.latestReviewByUser.set(reviewerName, review);
        this.emitDomainEvent("review.submitted", {
            pullRequest: number,
            reviewer: reviewerName,
            state,
            reviewedHead: pr.sourceHead
        });

        return review;
    }

    dismissReview(number, reviewerName) {
        const pr = this.requirePullRequest(number);
        const existing = pr.latestReviewByUser.get(reviewerName);

        if (!existing) {
            throw new WorkflowError("No review exists for this reviewer.");
        }

        const dismissal = Object.freeze({
            reviewer: reviewerName,
            state: ReviewState.DISMISSED,
            reviewedHead: existing.reviewedHead,
            sequence: ++this.sequence,
            submittedAt: new Date().toISOString()
        });

        pr.reviews.push(dismissal);
        pr.latestReviewByUser.set(reviewerName, dismissal);

        this.emitDomainEvent("review.dismissed", {
            pullRequest: number,
            reviewer: reviewerName
        });
    }

    addReviewThread(number, threadId, path, line, createdBy) {
        const pr = this.requirePullRequest(number);
        validateName(threadId, "Thread ID");
        validatePath(path);
        validateName(createdBy, "Thread creator");

        if (!Number.isInteger(line) || line < 1) {
            throw new TypeError("Thread line must be a positive integer.");
        }
        if (pr.threads.has(threadId)) {
            throw new WorkflowError(`Thread '${threadId}' already exists.`);
        }

        pr.threads.set(threadId, {
            threadId,
            path,
            line,
            createdBy,
            resolved: false,
            resolvedBy: null
        });

        this.emitDomainEvent("review.thread_created", {
            pullRequest: number,
            threadId,
            path,
            line
        });
    }

    resolveThread(number, threadId, actor) {
        const pr = this.requirePullRequest(number);
        const thread = pr.threads.get(threadId);

        if (!thread) {
            throw new WorkflowError(`Thread '${threadId}' does not exist.`);
        }
        validateName(actor, "Resolver");

        thread.resolved = true;
        thread.resolvedBy = actor;
        this.emitDomainEvent("review.thread_resolved", {
            pullRequest: number,
            threadId,
            actor
        });
    }

    recordCheck(number, checkName, state, details = "") {
        const pr = this.requirePullRequest(number);
        validateName(checkName, "Check name");

        if (!Object.values(CheckState).includes(state)) {
            throw new TypeError(`Invalid status-check state: ${state}`);
        }

        const key = `${pr.sourceHead}:${checkName}`;
        const check = Object.freeze({
            name: checkName,
            head: pr.sourceHead,
            state,
            details,
            completedAt: new Date().toISOString()
        });

        pr.checks.set(key, check);
        this.emitDomainEvent("status_check.recorded", {
            pullRequest: number,
            checkName,
            head: pr.sourceHead,
            state
        });
    }

    getCurrentApprovals(pr) {
        const approved = [];

        for (const [username, review] of pr.latestReviewByUser.entries()) {
            const reviewer = this.reviewers.get(username);

            if (
                reviewer &&
                reviewer.active &&
                reviewer.canReview &&
                username !== pr.author &&
                review.state === ReviewState.APPROVED &&
                review.reviewedHead === pr.sourceHead
            ) {
                approved.push(username);
            }
        }

        return approved.sort();
    }

    async evaluateMerge(number, strategy, actor) {
        const pr = this.requirePullRequest(number);
        const source = this.requireBranch(pr.source);
        const target = this.requireBranch(pr.target);
        const reviewer = this.reviewers.get(actor);
        const approvals = this.getCurrentApprovals(pr);
        const reasons = [];

        if (pr.state !== PRState.OPEN || pr.draft) {
            reasons.push("Pull Request must be open and ready.");
        }
        if (source.head !== pr.sourceHead) {
            reasons.push("Source branch changed after the recorded Pull Request head.");
        }
        if (target.head !== pr.baseHeadAtSync) {
            reasons.push("Target branch advanced; synchronize the base branch.");
        }

        const bypass = Boolean(
            reviewer &&
            reviewer.active &&
            reviewer.administrator &&
            this.policy.allowAdminBypass
        );

        if (!bypass) {
            if (approvals.length < this.policy.minimumApprovals) {
                reasons.push(
                    `Requires ${this.policy.minimumApprovals} current approvals; found ${approvals.length}.`
                );
            }

            const changeRequests = [...pr.latestReviewByUser.values()].some(review =>
                review.state === ReviewState.CHANGES_REQUESTED &&
                review.reviewedHead === pr.sourceHead
            );

            if (changeRequests) {
                reasons.push("A current review requests changes.");
            }

            // Independent checks run concurrently and are tied to the exact source head.
            const checkResults = await Promise.all(
                [...this.policy.requiredChecks].map(async name => {
                    const check = pr.checks.get(`${pr.sourceHead}:${name}`);
                    return {
                        name,
                        passed: Boolean(check && check.state === CheckState.PASSED)
                    };
                })
            );

            for (const result of checkResults) {
                if (!result.passed) {
                    reasons.push(`Required check '${result.name}' has not passed on the current head.`);
                }
            }

            if (this.policy.requireConversationResolution) {
                const unresolved = [...pr.threads.values()]
                    .filter(thread => !thread.resolved)
                    .map(thread => thread.threadId);

                if (unresolved.length > 0) {
                    reasons.push(`Unresolved conversations: ${unresolved.join(", ")}.`);
                }
            }

            const strategyAllowed = {
                [MergeStrategy.MERGE_COMMIT]: this.policy.allowMergeCommit,
                [MergeStrategy.SQUASH]: this.policy.allowSquash,
                [MergeStrategy.REBASE]: this.policy.allowRebase
            }[strategy];

            if (strategyAllowed !== true) {
                reasons.push(`Merge strategy '${strategy}' is not permitted.`);
            }
            if (
                this.policy.requireLinearHistory &&
                strategy === MergeStrategy.MERGE_COMMIT
            ) {
                reasons.push("A merge commit violates the linear-history requirement.");
            }
        }

        return Object.freeze({
            eligible: reasons.length === 0,
            reasons: Object.freeze(reasons),
            approvals: Object.freeze(approvals),
            bypassed: bypass
        });
    }

    async mergePullRequest(number, strategy, actor) {
        const decision = await this.evaluateMerge(number, strategy, actor);

        if (!decision.eligible) {
            throw new WorkflowError(
                `Merge blocked:\n${decision.reasons.map(reason => `- ${reason}`).join("\n")}`,
                "MERGE_BLOCKED"
            );
        }

        const pr = this.requirePullRequest(number);
        const source = this.requireBranch(pr.source);
        const target = this.requireBranch(pr.target);
        const parents = strategy === MergeStrategy.MERGE_COMMIT
            ? [target.head, source.head]
            : [target.head];

        const merged = this.createCommit(
            parents,
            `Merge PR #${number} using ${strategy}`,
            source.tree
        );

        target.head = merged.sha;
        target.tree = new Map(merged.tree);
        pr.state = PRState.MERGED;
        pr.mergeResult = Object.freeze({
            sha: merged.sha,
            strategy,
            mergedAt: new Date().toISOString()
        });

        this.emitDomainEvent("pull_request.merged", {
            pullRequest: number,
            strategy,
            mergeCommit: merged.sha,
            actor
        });

        return pr.mergeResult;
    }

    deleteBranch(branchName, actor) {
        const branch = this.requireBranch(branchName);

        if (branchName === "main") {
            throw new WorkflowError("The default branch cannot be deleted.");
        }
        if (branch.protected && this.policy.prohibitBranchDeletion) {
            throw new WorkflowError(`Deletion of protected branch '${branchName}' is blocked.`);
        }
        if (!this.reviewers.get(actor)?.active) {
            throw new WorkflowError("An active repository member is required.");
        }

        branch.deleted = true;
        this.emitDomainEvent("branch.deleted", { branch: branchName, actor });
    }
}

async function main() {
    const repository = new RepositoryGovernance(
        "orders-platform",
        new Map([
            ["README.md", "Orders platform"],
            ["src/order.js", "function createOrder(input) { return input; }"]
        ]),
        {
            minimumApprovals: 2,
            requiredChecks: ["unit-tests", "security-scan"],
            requireConversationResolution: true,
            requireLinearHistory: true,
            allowMergeCommit: false,
            allowSquash: true,
            allowRebase: true,
            allowDirectPush: false,
            allowForcePush: false,
            prohibitBranchDeletion: true
        }
    );

    repository.on("pull_request.merged", event => {
        process.stdout.write(`Event received: PR #${event.pullRequest} merged.\n`);
    });

    repository.registerReviewer("alice", { administrator: true });
    repository.registerReviewer("bob");
    repository.registerReviewer("carol");
    repository.registerReviewer("eve", { canReview: false });

    repository.createBranch("feature/order-validation");
    repository.commitToBranch(
        "feature/order-validation",
        "alice",
        "Validate order quantity",
        new Map([
            ["src/order.js", "function createOrder(input) {\n  if (!input.quantity || input.quantity < 1) throw new Error('Invalid quantity');\n  return input;\n}"]
        ])
    );

    repository.openPullRequest({
        number: 73,
        author: "alice",
        source: "feature/order-validation",
        target: "main",
        draft: true
    });

    repository.markReady(73);
    repository.addReviewThread(73, "discussion-1", "src/order.js", 2, "bob");

    repository.submitReview(73, "bob", ReviewState.APPROVED);
    repository.submitReview(73, "carol", ReviewState.APPROVED);
    repository.recordCheck(73, "unit-tests", CheckState.PASSED);
    repository.recordCheck(73, "security-scan", CheckState.PASSED);

    // An update to the source head automatically makes earlier review decisions stale.
    repository.commitToBranch(
        "feature/order-validation",
        "alice",
        "Add quantity boundary test",
        new Map([["tests/order.test.js", "assert.equal(createOrder({quantity: 1}).quantity, 1);"]])
    );

    const stale = await repository.evaluateMerge(73, MergeStrategy.SQUASH, "alice");
    console.log("Eligibility after source update:", stale.eligible);
    console.log("Reasons:", stale.reasons);

    repository.submitReview(73, "bob", ReviewState.APPROVED);
    repository.submitReview(73, "carol", ReviewState.APPROVED);
    repository.recordCheck(73, "unit-tests", CheckState.PASSED);
    repository.recordCheck(73, "security-scan", CheckState.PASSED);
    repository.resolveThread(73, "discussion-1", "alice");

    const decision = await repository.evaluateMerge(73, MergeStrategy.SQUASH, "alice");
    console.log("\nFinal eligibility:", decision.eligible);
    console.log("Current approvals:", decision.approvals);

    if (decision.eligible) {
        const result = await repository.mergePullRequest(
            73,
            MergeStrategy.SQUASH,
            "alice"
        );
        console.log("Merged commit:", result.sha);
        console.log("Pull Request state:", repository.requirePullRequest(73).state);
    }

    try {
        repository.submitReview(73, "eve", ReviewState.APPROVED);
    } catch (error) {
        console.log("\nExpected reviewer rejection:", error.message);
    }

    try {
        repository.commitToBranch(
            "main",
            "alice",
            "Attempt direct push",
            new Map([["README.md", "Unauthorized update"]])
        );
    } catch (error) {
        console.log("Expected protected-branch rejection:", error.message);
    }

    console.log("\nRecorded repository events:", repository.eventLog.length);
}

main().catch(error => {
    console.error(error);
    process.exitCode = 1;
});
