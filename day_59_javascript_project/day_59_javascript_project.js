'use strict';

const { EventEmitter } = require('node:events');
const crypto = require('node:crypto');

const PRState = Object.freeze({
  DRAFT: 'draft',
  OPEN: 'open',
  CLOSED: 'closed',
  MERGED: 'merged'
});

const ReviewState = Object.freeze({
  COMMENTED: 'commented',
  APPROVED: 'approved',
  CHANGES_REQUESTED: 'changes_requested',
  DISMISSED: 'dismissed'
});

const CheckState = Object.freeze({
  PENDING: 'pending',
  PASSING: 'passing',
  FAILING: 'failing'
});

const TaskState = Object.freeze({
  TODO: 'todo',
  IN_PROGRESS: 'in_progress',
  DONE: 'done'
});

function id(prefix) {
  return `${prefix}_${crypto.randomUUID().replaceAll('-', '').slice(0, 10)}`;
}

function now() {
  return new Date().toISOString();
}

class DomainError extends Error {}

class TaskManager extends EventEmitter {
  constructor(repositoryName) {
    super();
    this.repositoryName = repositoryName;
    this.branches = new Map();
    this.pullRequests = new Map();
    this.tasks = new Map();
    this.protection = new Map();
    this.nextPrNumber = 1;

    this.on('task.updated', event => {
      console.log(
        `[event] task ${event.task.id}: ${event.previous} -> ${event.task.state}`
      );
    });

    this.on('pr.reviewed', event => {
      console.log(
        `[event] PR #${event.pr.number} reviewed by ${event.reviewer}: ${event.state}`
      );
    });

    this.on('pr.merged', event => {
      console.log(`[event] PR #${event.pr.number} merged as ${event.strategy}`);
    });
  }

  createBranch(name, base = null) {
    if (this.branches.has(name)) {
      throw new DomainError(`Branch already exists: ${name}`);
    }

    const commits = base
      ? structuredClone(this.getBranch(base).commits)
      : [];

    this.branches.set(name, {
      name,
      protected: false,
      commits
    });
  }

  protectBranch(name, policy) {
    const branch = this.getBranch(name);

    const normalized = {
      requiredReviews: Math.max(0, Number(policy.requiredReviews ?? 1)),
      requiredStatusChecks: new Set(policy.requiredStatusChecks ?? []),
      restrictDirectPush: policy.restrictDirectPush !== false,
      restrictForcePush: policy.restrictForcePush !== false,
      restrictDeletion: policy.restrictDeletion !== false,
      requireConversationResolution:
        policy.requireConversationResolution !== false,
      requireLinearHistory: policy.requireLinearHistory === true,
      allowAdministratorBypass: policy.allowAdministratorBypass === true
    };

    branch.protected = true;
    this.protection.set(name, normalized);
  }

  commit(branchName, author, message) {
    const branch = this.getBranch(branchName);

    if (!author?.trim()) {
      throw new DomainError('Commit author is required.');
    }

    if (!message?.trim()) {
      throw new DomainError('Commit message is required.');
    }

    const commit = {
      sha: id('sha'),
      author: author.trim(),
      message: message.trim(),
      timestamp: now()
    };

    branch.commits.push(commit);
    return commit;
  }

  createTask(title, description, priority = 'medium') {
    const priorities = new Set(['low', 'medium', 'high', 'critical']);

    if (!title?.trim()) {
      throw new DomainError('Task title is required.');
    }

    if (!priorities.has(priority)) {
      throw new DomainError(`Invalid task priority: ${priority}`);
    }

    const task = {
      id: id('task'),
      title: title.trim(),
      description: description?.trim() ?? '',
      priority,
      state: TaskState.TODO,
      linkedPr: null,
      createdAt: now()
    };

    this.tasks.set(task.id, task);
    this.emit('task.created', { task });
    return task;
  }

  updateTask(taskId, state) {
    const task = this.tasks.get(taskId);

    if (!task) {
      throw new DomainError('Task not found.');
    }

    if (!Object.values(TaskState).includes(state)) {
      throw new DomainError(`Invalid task state: ${state}`);
    }

    const previous = task.state;
    task.state = state;

    this.emit('task.updated', { task, previous });
    return task;
  }

  linkTask(taskId, prNumber) {
    const task = this.tasks.get(taskId);
    const pr = this.getPr(prNumber);

    if (!task) {
      throw new DomainError('Task not found.');
    }

    task.linkedPr = pr.number;
  }

  createPullRequest({
    title,
    sourceBranch,
    targetBranch,
    author,
    draft = false
  }) {
    this.getBranch(sourceBranch);
    this.getBranch(targetBranch);

    if (sourceBranch === targetBranch) {
      throw new DomainError('Source and target branches must differ.');
    }

    if (!title?.trim()) {
      throw new DomainError('Pull request title is required.');
    }

    const source = this.getBranch(sourceBranch);

    if (source.commits.length === 0) {
      throw new DomainError('A pull request requires at least one commit.');
    }

    const pr = {
      number: this.nextPrNumber++,
      title: title.trim(),
      sourceBranch,
      targetBranch,
      author,
      state: draft ? PRState.DRAFT : PRState.OPEN,
      commits: structuredClone(source.commits),
      requestedReviewers: new Set(),
      reviews: [],
      checks: new Map(),
      conversations: [],
      mergeStrategy: null
    };

    this.pullRequests.set(pr.number, pr);
    this.emit('pr.created', { pr });
    return pr;
  }

  markReady(prNumber) {
    const pr = this.getPr(prNumber);

    if (pr.state !== PRState.DRAFT) {
      throw new DomainError('Only draft PRs can become ready.');
    }

    pr.state = PRState.OPEN;
    this.emit('pr.ready', { pr });
  }

  requestReview(prNumber, reviewer) {
    const pr = this.getPr(prNumber);

    if (![PRState.DRAFT, PRState.OPEN].includes(pr.state)) {
      throw new DomainError('Reviewer cannot be requested for this PR.');
    }

    if (!reviewer?.trim() || reviewer === pr.author) {
      throw new DomainError('A valid reviewer different from the author is required.');
    }

    pr.requestedReviewers.add(reviewer);
  }

  submitReview(prNumber, reviewer, state, body = '') {
    const pr = this.getPr(prNumber);

    if (pr.state !== PRState.OPEN) {
      throw new DomainError('Only open PRs can receive reviews.');
    }

    if (!pr.requestedReviewers.has(reviewer)) {
      throw new DomainError('Reviewer was not requested.');
    }

    if (reviewer === pr.author) {
      throw new DomainError('Authors cannot review their own PR.');
    }

    if (!Object.values(ReviewState).includes(state)) {
      throw new DomainError(`Invalid review state: ${state}`);
    }

    const review = {
      id: id('review'),
      reviewer,
      state,
      body: body.trim(),
      commitSha: this.headSha(pr),
      submittedAt: now(),
      dismissed: false,
      comments: []
    };

    pr.reviews.push(review);
    this.emit('pr.reviewed', {
      pr,
      reviewer,
      state
    });

    return review;
  }

  addConversation(prNumber, reviewer, body) {
    const pr = this.getPr(prNumber);

    if (!body?.trim()) {
      throw new DomainError('Conversation body cannot be empty.');
    }

    const conversation = {
      id: id('conversation'),
      reviewer,
      body: body.trim(),
      resolved: false,
      createdAt: now()
    };

    pr.conversations.push(conversation);
    return conversation;
  }

  resolveConversation(prNumber, conversationId) {
    const pr = this.getPr(prNumber);
    const conversation = pr.conversations.find(c => c.id === conversationId);

    if (!conversation) {
      throw new DomainError('Conversation not found.');
    }

    conversation.resolved = true;
  }

  setCheck(prNumber, name, state) {
    const pr = this.getPr(prNumber);

    if (!Object.values(CheckState).includes(state)) {
      throw new DomainError(`Invalid status state: ${state}`);
    }

    pr.checks.set(name, {
      name,
      state,
      commitSha: this.headSha(pr),
      completedAt: now()
    });
  }

  synchronize(prNumber) {
    const pr = this.getPr(prNumber);
    const source = this.getBranch(pr.sourceBranch);
    const target = this.getBranch(pr.targetBranch);

    const sourceShas = new Set(source.commits.map(commit => commit.sha));

    for (const commit of target.commits) {
      if (!sourceShas.has(commit.sha)) {
        source.commits.push(structuredClone(commit));
      }
    }

    pr.commits = structuredClone(source.commits);
    return this.headSha(pr);
  }

  evaluateMerge(prNumber, actor, administrator = false) {
    const pr = this.getPr(prNumber);
    const policy = this.protection.get(pr.targetBranch);
    const reasons = [];

    if (pr.state !== PRState.OPEN) {
      reasons.push(`PR state is ${pr.state}`);
    }

    if (!pr.commits.length) {
      reasons.push('PR has no commits');
    }

    if (!policy) {
      return { eligible: reasons.length === 0, reasons };
    }

    if (actor === pr.author) {
      reasons.push('author cannot merge its own PR');
    }

    const bypass = administrator && policy.allowAdministratorBypass;

    if (!bypass) {
      const head = this.headSha(pr);

      const currentApprovals = new Set(
        pr.reviews
          .filter(
            review =>
              review.state === ReviewState.APPROVED &&
              !review.dismissed &&
              review.commitSha === head
          )
          .map(review => review.reviewer)
      );

      if (currentApprovals.size < policy.requiredReviews) {
        reasons.push(
          `requires ${policy.requiredReviews} current approval(s), found ${currentApprovals.size}`
        );
      }

      for (const required of policy.requiredStatusChecks) {
        const check = pr.checks.get(required);

        if (!check || check.state !== CheckState.PASSING) {
          reasons.push(`required check is not passing: ${required}`);
        } else if (check.commitSha !== head) {
          reasons.push(`status check is stale: ${required}`);
        }
      }

      if (policy.requireConversationResolution) {
        const unresolved = pr.conversations.filter(c => !c.resolved).length;
        if (unresolved > 0) {
          reasons.push(`${unresolved} conversation(s) unresolved`);
        }
      }
    }

    return {
      eligible: reasons.length === 0,
      reasons
    };
  }

  merge(prNumber, actor, strategy = 'squash', administrator = false) {
    const pr = this.getPr(prNumber);
    const result = this.evaluateMerge(prNumber, actor, administrator);

    if (!result.eligible) {
      throw new DomainError(`Merge blocked: ${result.reasons.join('; ')}`);
    }

    if (!['merge', 'squash', 'rebase'].includes(strategy)) {
      throw new DomainError('Unsupported merge strategy.');
    }

    const target = this.getBranch(pr.targetBranch);

    const commit = {
      sha: id('sha'),
      author: actor,
      message: `${strategy} merge PR #${pr.number}: ${pr.title}`,
      timestamp: now()
    };

    target.commits.push(commit);
    pr.state = PRState.MERGED;
    pr.mergeStrategy = strategy;

    this.emit('pr.merged', {
      pr,
      strategy,
      commit
    });

    return commit;
  }

  dashboard() {
    return {
      repository: this.repositoryName,
      tasks: [...this.tasks.values()].map(task => ({
        id: task.id,
        title: task.title,
        state: task.state,
        priority: task.priority,
        linkedPr: task.linkedPr
      })),
      pullRequests: [...this.pullRequests.values()].map(pr => ({
        number: pr.number,
        title: pr.title,
        state: pr.state,
        source: pr.sourceBranch,
        target: pr.targetBranch,
        reviews: pr.reviews.length,
        checks: Object.fromEntries(
          [...pr.checks.entries()].map(([name, check]) => [name, check.state])
        ),
        mergeEligibility: this.evaluateMerge(
          pr.number,
          'release-manager'
        )
      }))
    };
  }

  headSha(pr) {
    return pr.commits.at(-1)?.sha ?? null;
  }

  getBranch(name) {
    const branch = this.branches.get(name);
    if (!branch) {
      throw new DomainError(`Unknown branch: ${name}`);
    }
    return branch;
  }

  getPr(number) {
    const pr = this.pullRequests.get(number);
    if (!pr) {
      throw new DomainError(`Unknown pull request: ${number}`);
    }
    return pr;
  }
}

async function runDemo() {
  const manager = new TaskManager('interactive-task-manager');

  manager.createBranch('main');
  manager.commit('main', 'admin', 'Initialize task management platform');

  manager.protectBranch('main', {
    requiredReviews: 2,
    requiredStatusChecks: ['unit-tests', 'security-scan'],
    restrictDirectPush: true,
    restrictForcePush: true,
    restrictDeletion: true,
    requireConversationResolution: true,
    requireLinearHistory: true,
    allowAdministratorBypass: false
  });

  manager.createBranch('feature/task-board', 'main');
  manager.commit(
    'feature/task-board',
    'developer',
    'Add interactive task board state model'
  );
  manager.commit(
    'feature/task-board',
    'developer',
    'Add task filtering and PR linkage'
  );

  const task = manager.createTask(
    'Build protected task workflow',
    'Track engineering tasks and require governed PR merges.',
    'high'
  );

  const pr = manager.createPullRequest({
    title: 'Build protected task workflow',
    sourceBranch: 'feature/task-board',
    targetBranch: 'main',
    author: 'developer',
    draft: true
  });

  manager.linkTask(task.id, pr.number);
  manager.markReady(pr.number);

  manager.requestReview(pr.number, 'reviewer-one');
  manager.requestReview(pr.number, 'reviewer-two');

  const firstReview = manager.submitReview(
    pr.number,
    'reviewer-one',
    ReviewState.CHANGES_REQUESTED,
    'Validate task state transitions before persistence.'
  );

  const conversation = manager.addConversation(
    pr.number,
    firstReview.reviewer,
    'State transitions should reject invalid values.'
  );

  let eligibility = manager.evaluateMerge(pr.number, 'release-manager');
  if (eligibility.eligible) {
    throw new Error('PR should initially be blocked.');
  }

  manager.resolveConversation(pr.number, conversation.id);

  manager.submitReview(
    pr.number,
    'reviewer-one',
    ReviewState.APPROVED,
    'Validation is now acceptable.'
  );

  manager.submitReview(
    pr.number,
    'reviewer-two',
    ReviewState.APPROVED,
    'Reviewed implementation and tests.'
  );

  manager.setCheck(pr.number, 'unit-tests', CheckState.PASSING);
  manager.setCheck(pr.number, 'security-scan', CheckState.PASSING);

  eligibility = manager.evaluateMerge(pr.number, 'release-manager');

  if (!eligibility.eligible) {
    throw new Error(`Expected merge eligibility: ${eligibility.reasons.join(', ')}`);
  }

  await Promise.resolve();
  manager.merge(pr.number, 'release-manager', 'squash');
  manager.updateTask(task.id, TaskState.DONE);

  console.log('\nInteractive task-management dashboard:\n');
  console.log(JSON.stringify(manager.dashboard(), null, 2));
}

runDemo().catch(error => {
  console.error(`Application failure: ${error.message}`);
  process.exitCode = 1;
});
