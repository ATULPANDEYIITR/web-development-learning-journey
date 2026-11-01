"use strict";

const EventEmitter = require("node:events");

const PRState = Object.freeze({
  DRAFT: "draft",
  OPEN: "open",
  CLOSED: "closed",
  MERGED: "merged"
});

const ReviewState = Object.freeze({
  COMMENTED: "commented",
  APPROVED: "approved",
  CHANGES_REQUESTED: "changes_requested",
  DISMISSED: "dismissed"
});

const CheckState = Object.freeze({
  PENDING: "pending",
  PASSED: "passed",
  FAILED: "failed"
});

const MergeStrategy = Object.freeze({
  MERGE: "merge",
  SQUASH: "squash",
  REBASE: "rebase"
});

class ValidationError extends Error {}
class AuthorizationError extends Error {}
class MergeBlockedError extends Error {}

class Commit {
  constructor(sha, message, author) {
    if (!/^[A-Za-z0-9._-]+$/.test(sha)) {
      throw new ValidationError("Invalid commit identifier");
    }
    if (!message.trim() || !author.trim()) {
      throw new ValidationError("Commit message and author are required");
    }
    this.sha = sha;
    this.message = message;
    this.author = author;
  }
}

class Branch {
  constructor(name, commits = []) {
    this.name = name;
    this.commits = [...commits];
    this.protected = false;
  }

  get head() {
    return this.commits.at(-1)?.sha ?? null;
  }

  addCommit(commit) {
    if (this.commits.some(existing => existing.sha === commit.sha)) {
      throw new ValidationError(`Commit ${commit.sha} already exists`);
    }
    this.commits.push(commit);
  }
}

class PullRequest {
  constructor(number, title, source, target, author, draft = false) {
    this.number = number;
    this.title = title;
    this.source = source;
    this.target = target;
    this.author = author;
    this.state = draft ? PRState.DRAFT : PRState.OPEN;
    this.draft = draft;
    this.commits = [];
    this.reviews = [];
    this.comments = [];
    this.checks = new Map();
    this.baseHead = null;
  }

  addReview(review) {
    if (this.state !== PRState.OPEN) {
      throw new ValidationError("Reviews require an open pull request");
    }
    this.reviews.push(review);
  }

  addComment(comment) {
    if (!comment.body.trim()) {
      throw new ValidationError("Review comment cannot be empty");
    }
    this.comments.push({ ...comment, resolved: false });
  }

  setCheck(name, state) {
    if (!Object.values(CheckState).includes(state)) {
      throw new ValidationError(`Unknown status state: ${state}`);
    }
    this.checks.set(name, state);
  }
}

class Repository extends EventEmitter {
  constructor(name) {
    super();
    this.name = name;
    this.defaultBranch = "main";
    this.branches = new Map();
    this.pullRequests = new Map();
    this.issues = new Map();
    this.protection = new Map();
    this.nextPR = 1;
    this.nextIssue = 1;
  }

  createBranch(name, from = null) {
    if (this.branches.has(name)) {
      throw new ValidationError(`Branch ${name} already exists`);
    }

    let commits = [];
    if (from !== null) {
      const source = this.branches.get(from);
      if (!source) throw new ValidationError(`Unknown branch ${from}`);
      commits = [...source.commits];
    }

    this.branches.set(name, new Branch(name, commits));
    this.emit("branchCreated", { repository: this.name, branch: name });
  }

  configureProtection(branchName, policy) {
    const branch = this.branches.get(branchName);
    if (!branch) throw new ValidationError("Protection target does not exist");

    const normalized = {
      requiredReviews: Number(policy.requiredReviews ?? 1),
      requiredChecks: new Set(policy.requiredChecks ?? []),
      dismissStaleApprovals: policy.dismissStaleApprovals ?? true,
      requireConversationResolution:
        policy.requireConversationResolution ?? true,
      allowDirectPush: policy.allowDirectPush ?? false,
      allowForcePush: policy.allowForcePush ?? false
    };

    if (normalized.requiredReviews < 0) {
      throw new ValidationError("Required reviews cannot be negative");
    }

    branch.protected = true;
    this.protection.set(branchName, normalized);
  }

  createPullRequest({ title, source, target, author, draft = false }) {
    if (!this.branches.has(source) || !this.branches.has(target)) {
      throw new ValidationError("Source and target branches must exist");
    }
    if (source === target) {
      throw new ValidationError("Source and target must differ");
    }

    const pr = new PullRequest(
      this.nextPR++,
      title,
      source,
      target,
      author,
      draft
    );

    pr.commits = [...this.branches.get(source).commits];
    pr.baseHead = this.branches.get(target).head;
    this.pullRequests.set(pr.number, pr);

    this.emit("pullRequestCreated", {
      repository: this.name,
      number: pr.number
    });

    return pr;
  }

  approve(pr, reviewer) {
    if (reviewer === pr.author) {
      throw new AuthorizationError("Self-approval is not permitted");
    }

    pr.addReview({
      reviewer,
      state: ReviewState.APPROVED,
      timestamp: new Date().toISOString()
    });

    this.emit("reviewSubmitted", {
      pr: pr.number,
      reviewer,
      state: ReviewState.APPROVED
    });
  }

  requestChanges(pr, reviewer, body) {
    pr.addReview({
      reviewer,
      state: ReviewState.CHANGES_REQUESTED,
      body,
      timestamp: new Date().toISOString()
    });

    this.emit("reviewSubmitted", {
      pr: pr.number,
      reviewer,
      state: ReviewState.CHANGES_REQUESTED
    });
  }

  evaluateMerge(pr) {
    const reasons = [];

    if (pr.state !== PRState.OPEN) reasons.push("Pull request is not open");
    if (pr.draft) reasons.push("Pull request is a draft");
    if (pr.commits.length === 0) reasons.push("No commits are proposed");

    const policy = this.protection.get(pr.target);

    if (policy) {
      const approvals = new Set(
        pr.reviews
          .filter(review => review.state === ReviewState.APPROVED)
          .map(review => review.reviewer)
      );

      if (approvals.size < policy.requiredReviews) {
        reasons.push(
          `Requires ${policy.requiredReviews} approval(s), has ${approvals.size}`
        );
      }

      for (const check of policy.requiredChecks) {
        if (pr.checks.get(check) !== CheckState.PASSED) {
          reasons.push(`Required check '${check}' is not passing`);
        }
      }

      if (
        policy.requireConversationResolution &&
        pr.comments.some(comment => !comment.resolved)
      ) {
        reasons.push("Unresolved review conversations exist");
      }

      if (
        pr.reviews.some(
          review => review.state === ReviewState.CHANGES_REQUESTED
        )
      ) {
        reasons.push("A reviewer has requested changes");
      }
    }

    return {
      eligible: reasons.length === 0,
      reasons
    };
  }

  merge(pr, strategy = MergeStrategy.SQUASH) {
    const evaluation = this.evaluateMerge(pr);
    if (!evaluation.eligible) {
      throw new MergeBlockedError(evaluation.reasons.join("; "));
    }

    const target = this.branches.get(pr.target);

    if (strategy === MergeStrategy.SQUASH) {
      target.addCommit(
        new Commit(
          `squash-${pr.number}`,
          `Squash merge PR #${pr.number}: ${pr.title}`,
          pr.author
        )
      );
    } else if (strategy === MergeStrategy.MERGE) {
      target.addCommit(
        new Commit(
          `merge-${pr.number}`,
          `Merge PR #${pr.number}: ${pr.title}`,
          pr.author
        )
      );
    } else {
      for (const commit of pr.commits) {
        target.addCommit(
          new Commit(
            `rebased-${commit.sha}`,
            commit.message,
            commit.author
          )
        );
      }
    }

    pr.state = PRState.MERGED;

    this.emit("pullRequestMerged", {
      number: pr.number,
      strategy,
      target: pr.target
    });
  }

  directPush(branchName, commits) {
    const branch = this.branches.get(branchName);
    if (!branch) throw new ValidationError("Unknown branch");

    const policy = this.protection.get(branchName);

    if (branch.protected && policy && !policy.allowDirectPush) {
      throw new AuthorizationError(
        `Direct push to protected branch '${branchName}' is blocked`
      );
    }

    for (const commit of commits) branch.addCommit(commit);
    this.emit("directPush", { branch: branchName });
  }

  clone() {
    const clone = new Repository(this.name);

    for (const [name, branch] of this.branches) {
      clone.branches.set(
        name,
        new Branch(name, [...branch.commits])
      );
      clone.branches.get(name).protected = branch.protected;
    }

    for (const [name, policy] of this.protection) {
      clone.protection.set(name, {
        ...policy,
        requiredChecks: new Set(policy.requiredChecks)
      });
    }

    return clone;
  }

  pullFrom(remote, branchName) {
    const remoteBranch = remote.branches.get(branchName);
    if (!remoteBranch) {
      throw new ValidationError(`Remote branch '${branchName}' does not exist`);
    }

    this.branches.set(
      branchName,
      new Branch(branchName, [...remoteBranch.commits])
    );

    this.emit("pullCompleted", { branch: branchName });
  }

  createIssue(title, author, labels = []) {
    const issue = {
      number: this.nextIssue++,
      title,
      author,
      labels: new Set(labels),
      open: true
    };

    this.issues.set(issue.number, issue);
    this.emit("issueCreated", issue);
    return issue;
  }
}

async function runWorkflow() {
  const remote = new Repository("secure-api");

  remote.on("pullRequestCreated", event =>
    console.log(`Event: PR #${event.number} created`)
  );
  remote.on("reviewSubmitted", event =>
    console.log(
      `Event: ${event.reviewer} submitted ${event.state} on PR #${event.pr}`
    )
  );
  remote.on("pullRequestMerged", event =>
    console.log(`Event: PR #${event.number} merged using ${event.strategy}`)
  );

  remote.createBranch("main");
  remote.branches.get("main").addCommit(
    new Commit("a1", "Initial repository state", "alice")
  );

  remote.configureProtection("main", {
    requiredReviews: 2,
    requiredChecks: ["tests", "security"],
    dismissStaleApprovals: true,
    requireConversationResolution: true,
    allowDirectPush: false,
    allowForcePush: false
  });

  const local = remote.clone();

  local.createBranch("feature/git-workflow", "main");
  local.branches.get("feature/git-workflow").addCommit(
    new Commit("b1", "Document clone and pull operations", "bob")
  );

  local.branches.get("feature/git-workflow").addCommit(
    new Commit("b2", "Add remote repository examples", "bob")
  );

  const pr = remote.createPullRequest({
    title: "Document remote repository workflow",
    source: "feature/git-workflow",
    target: "main",
    author: "bob"
  });

  pr.addComment({
    reviewer: "carol",
    file: "README.md",
    line: 42,
    body: "Explain why direct pushes are restricted."
  });

  remote.approve(pr, "carol");
  remote.approve(pr, "david");

  pr.setCheck("tests", CheckState.PASSED);
  pr.setCheck("security", CheckState.PASSED);

  let evaluation = remote.evaluateMerge(pr);
  console.log("Before conversation resolution:", evaluation);

  for (const comment of pr.comments) {
    comment.resolved = true;
  }

  evaluation = remote.evaluateMerge(pr);
  console.log("After conversation resolution:", evaluation);

  if (evaluation.eligible) {
    remote.merge(pr, MergeStrategy.SQUASH);
  }

  const issue = remote.createIssue(
    "Clarify clone, pull, push, and README workflow",
    "alice",
    ["documentation", "git"]
  );

  console.log(`Created issue #${issue.number}: ${issue.title}`);

  try {
    local.branches.get("main").addCommit(
      new Commit("unauthorized", "Attempt direct protected push", "eve")
    );

    remote.directPush(
      "main",
      [local.branches.get("main").commits.at(-1)]
    );
  } catch (error) {
    if (error instanceof AuthorizationError) {
      console.log(`Expected protection failure: ${error.message}`);
    } else {
      throw error;
    }
  }

  local.pullFrom(remote, "main");

  if (local.branches.get("main").head !== remote.branches.get("main").head) {
    throw new Error("Pull synchronization failed");
  }

  console.log("\nRepository state:");
  for (const [name, branch] of remote.branches) {
    console.log(
      `${name}: head=${branch.head}, protected=${branch.protected}, commits=${branch.commits.length}`
    );
  }
}

runWorkflow().catch(error => {
  console.error(`Workflow failed: ${error.message}`);
  process.exitCode = 1;
});
