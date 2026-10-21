'use strict';

/*
 * Event-driven repository governance model.
 *
 * The implementation intentionally uses JavaScript callbacks, timers,
 * Promises, async functions, and the event loop to represent operations
 * that complete at different times.
 *
 * The governance domain remains distinct:
 *   Pull Request       -> proposes and transports changes
 *   Code Review        -> evaluates changes
 *   Approval           -> records an eligible review decision
 *   Branch Protection  -> enforces repository-level merge conditions
 */

const { EventEmitter } = require('node:events');

const PRState = Object.freeze({
  DRAFT: 'draft',
  OPEN: 'open',
  CLOSED: 'closed',
  MERGED: 'merged',
});

const ReviewState = Object.freeze({
  COMMENTED: 'commented',
  CHANGES_REQUESTED: 'changes_requested',
  APPROVED: 'approved',
  DISMISSED: 'dismissed',
});

class RepositoryError extends Error {}

class BranchProtection {
  constructor({
    requiredReviews,
    requiredStatusChecks,
    requireConversationResolution = true,
    requireLinearHistory = true,
    restrictDirectPush = true,
    restrictForcePush = true,
  }) {
    if (!Number.isInteger(requiredReviews) || requiredReviews < 0) {
      throw new TypeError('requiredReviews must be a non-negative integer');
    }

    this.requiredReviews = requiredReviews;
    this.requiredStatusChecks = new Set(requiredStatusChecks);
    this.requireConversationResolution = requireConversationResolution;
    this.requireLinearHistory = requireLinearHistory;
    this.restrictDirectPush = restrictDirectPush;
    this.restrictForcePush = restrictForcePush;
  }
}

class PullRequest extends EventEmitter {
  constructor(number, sourceBranch, targetBranch, commits, draft = false) {
    super();

    if (sourceBranch === targetBranch) {
      throw new RepositoryError('Source and target branches must differ');
    }
    if (!Array.isArray(commits) || commits.length === 0) {
      throw new RepositoryError('A Pull Request requires at least one commit');
    }

    this.number = number;
    this.sourceBranch = sourceBranch;
    this.targetBranch = targetBranch;
    this.commits = [...commits];
    this.state = draft ? PRState.DRAFT : PRState.OPEN;
    this.reviews = [];
    this.openConversations = 0;
    this.statusChecks = new Map();
  }

  get headSha() {
    return this.commits.at(-1).sha;
  }

  markReady() {
    if (this.state !== PRState.DRAFT) {
      throw new RepositoryError('Only draft Pull Requests can become ready');
    }
    this.state = PRState.OPEN;
    this.emit('ready', this);
  }

  addCommit(commit) {
    if (this.state !== PRState.OPEN) {
      throw new RepositoryError('Commits require an open Pull Request');
    }

    this.commits.push(commit);

    // A new head makes earlier approvals stale in this model.
    this.reviews = this.reviews.map((review) =>
      review.state === ReviewState.APPROVED
        ? { ...review, state: ReviewState.DISMISSED }
        : review
    );

    this.emit('synchronize', this);
  }

  addReview(reviewer, state, comments = []) {
    if (this.state !== PRState.OPEN) {
      throw new RepositoryError('Reviews require an open Pull Request');
    }
    if (!reviewer || typeof reviewer !== 'string') {
      throw new TypeError('Reviewer must be a non-empty string');
    }

    const review = {
      reviewer,
      state,
      commitSha: this.headSha,
      comments: [...comments],
    };

    this.reviews.push(review);
    this.emit('reviewSubmitted', review);
  }

  openConversation() {
    this.openConversations += 1;
    this.emit('conversationOpened');
  }

  resolveConversation() {
    if (this.openConversations === 0) {
      throw new RepositoryError('No unresolved conversation exists');
    }
    this.openConversations -= 1;
    this.emit('conversationResolved');
  }
}

class RepositoryGovernance {
  constructor(protection) {
    this.protection = protection;
    this.protectedBranches = new Set(['main']);
  }

  registerChecks(pr) {
    for (const check of this.protection.requiredStatusChecks) {
      pr.statusChecks.set(check, {
        name: check,
        state: 'queued',
        passed: false,
      });
    }
  }

  /*
   * Callback-based timer operation.
   *
   * setTimeout does not block the JavaScript thread. The callback is placed
   * into a future event-loop turn after the timer expires.
   */
  runCheckWithCallback(pr, name, callback) {
    const check = pr.statusChecks.get(name);
    if (!check) {
      callback(new RepositoryError(`Unknown check: ${name}`));
      return;
    }

    check.state = 'running';

    setTimeout(() => {
      if (name === 'security-scan') {
        check.passed = !pr.commits.some((commit) =>
          commit.message.toLowerCase().includes('secret')
        );
      } else {
        check.passed = pr.commits.length > 0;
      }

      check.state = 'completed';
      callback(null, check);
    }, name === 'security-scan' ? 140 : 80);
  }

  /*
   * Promise conversion makes callback-oriented infrastructure composable
   * with async/await without changing the underlying timer behavior.
   */
  runCheck(pr, name) {
    return new Promise((resolve, reject) => {
      this.runCheckWithCallback(pr, name, (error, result) => {
        if (error) reject(error);
        else resolve(result);
      });
    });
  }

  async runChecksConcurrently(pr) {
    // Promise.all starts both operations before waiting for either result.
    return Promise.all(
      [...this.protection.requiredStatusChecks].map((name) =>
        this.runCheck(pr, name)
      )
    );
  }

  evaluate(pr) {
    const failures = [];

    if (pr.state !== PRState.OPEN) {
      failures.push('Pull Request is not open');
    }

    for (const required of this.protection.requiredStatusChecks) {
      const check = pr.statusChecks.get(required);
      if (!check || !check.passed) {
        failures.push(`Required status check failed: ${required}`);
      }
    }

    const approvals = new Set(
      pr.reviews
        .filter(
          (review) =>
            review.state === ReviewState.APPROVED &&
            review.commitSha === pr.headSha
        )
        .map((review) => review.reviewer)
    );

    if (approvals.size < this.protection.requiredReviews) {
      failures.push(
        `Requires ${this.protection.requiredReviews} current approval(s); found ${approvals.size}`
      );
    }

    if (
      this.protection.requireConversationResolution &&
      pr.openConversations > 0
    ) {
      failures.push('Unresolved review conversations remain');
    }

    if (
      this.protection.requireLinearHistory &&
      pr.commits.some((commit) =>
        commit.message.toLowerCase().includes('merge commit')
      )
    ) {
      failures.push('Linear history is required');
    }

    return {
      eligible: failures.length === 0,
      failures,
    };
  }

  merge(pr) {
    const result = this.evaluate(pr);
    if (!result.eligible) {
      throw new RepositoryError(
        `Merge rejected: ${result.failures.join('; ')}`
      );
    }

    pr.state = PRState.MERGED;
    pr.emit('merged', pr);
  }
}

function demonstrateEventLoop() {
  console.log('synchronous: Pull Request object created');

  setTimeout(() => {
    console.log('timer callback: asynchronous review reminder');
  }, 0);

  Promise.resolve().then(() => {
    console.log('microtask: Promise continuation');
  });

  console.log('synchronous: current call stack continues');
}

async function main() {
  const protection = new BranchProtection({
    requiredReviews: 2,
    requiredStatusChecks: ['unit-tests', 'security-scan'],
  });

  const governance = new RepositoryGovernance(protection);

  const pr = new PullRequest(
    73,
    'feature/governance-engine',
    'main',
    [
      { sha: 'c101', message: 'Implement governance engine' },
      { sha: 'c102', message: 'Add asynchronous checks' },
    ],
    true
  );

  pr.on('ready', () => console.log('event: Pull Request marked ready'));
  pr.on('reviewSubmitted', (review) =>
    console.log(`event: review submitted by ${review.reviewer}`)
  );
  pr.on('synchronize', () =>
    console.log('event: source branch synchronized')
  );

  governance.registerChecks(pr);
  pr.markReady();

  pr.addReview('alice', ReviewState.APPROVED);
  pr.addReview('bob', ReviewState.COMMENTED, [
    'Please clarify the status-check failure policy.',
  ]);

  pr.addReview('bob', ReviewState.APPROVED);

  demonstrateEventLoop();

  await governance.runChecksConcurrently(pr);

  pr.openConversation();

  let result = governance.evaluate(pr);
  console.log('Eligible with unresolved conversation:', result.eligible);
  console.log('Failures:', result.failures);

  pr.resolveConversation();

  result = governance.evaluate(pr);
  console.log('Eligible after resolution:', result.eligible);

  if (result.eligible) {
    governance.merge(pr);
    console.log(`Pull Request #${pr.number} merged`);
  }
}

main().catch((error) => {
  console.error('Workflow failure:', error.message);
  process.exitCode = 1;
});
