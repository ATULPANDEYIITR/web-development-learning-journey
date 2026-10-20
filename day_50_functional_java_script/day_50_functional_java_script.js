'use strict';

/*
 * Functional JavaScript model of repository governance.
 *
 * The repository workflow is represented as immutable data. Operations return
 * new values instead of mutating existing objects. Policy checks are pure
 * functions, and higher-order functions are used to build reusable evaluators.
 */

const PullRequestState = Object.freeze({
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

const MergeStrategy = Object.freeze({
  MERGE_COMMIT: 'merge_commit',
  SQUASH: 'squash',
  REBASE: 'rebase'
});

const deepFreeze = value => {
  if (value && typeof value === 'object' && !Object.isFrozen(value)) {
    Object.freeze(value);
    Object.values(value).forEach(deepFreeze);
  }
  return value;
};

const pipe = (...functions) => value =>
  functions.reduce((current, fn) => fn(current), value);

const compose = (...functions) => value =>
  functions.reduceRight((current, fn) => fn(current), value);

const map = fn => values => values.map(fn);
const filter = predicate => values => values.filter(predicate);
const reduce = (fn, initial) => values => values.reduce(fn, initial);

const normalizeCommit = commit => ({
  ...commit,
  message: commit.message.trim().replace(/\s+/g, ' ')
});

const meaningfulCommit = commit => commit.message.length >= 8;

const commitLabel = commit => `${commit.sha}: ${commit.message}`;

const functionalCommitPipeline = pipe(
  map(normalizeCommit),
  filter(meaningfulCommit),
  map(commitLabel)
);

const createReview = ({
  reviewer,
  state,
  comments = []
}) => {
  if (typeof reviewer !== 'string' || reviewer.trim() === '') {
    throw new TypeError('reviewer must be a non-empty string');
  }

  if (!Object.values(ReviewState).includes(state)) {
    throw new RangeError(`invalid review state: ${state}`);
  }

  return deepFreeze({
    reviewer: reviewer.trim(),
    state,
    comments: [...comments]
  });
};

const createStatusCheck = (name, passed, required = true) => {
  if (typeof name !== 'string' || name.trim() === '') {
    throw new TypeError('status-check name must be non-empty');
  }

  return deepFreeze({
    name: name.trim(),
    passed: Boolean(passed),
    required: Boolean(required)
  });
};

const createPolicy = ({
  requiredReviews = 1,
  requiredChecks = [],
  requireConversationResolution = true,
  requireLinearHistory = false,
  allowDirectPush = false,
  allowForcePush = false,
  allowDeletion = false,
  allowAdminBypass = false
} = {}) => {
  if (!Number.isInteger(requiredReviews) || requiredReviews < 0) {
    throw new RangeError('requiredReviews must be a non-negative integer');
  }

  return deepFreeze({
    requiredReviews,
    requiredChecks: [...requiredChecks],
    requireConversationResolution,
    requireLinearHistory,
    allowDirectPush,
    allowForcePush,
    allowDeletion,
    allowAdminBypass
  });
};

const createPullRequest = ({
  number,
  sourceBranch,
  targetBranch,
  commits,
  state = PullRequestState.DRAFT,
  reviews = [],
  checks = [],
  unresolvedConversations = 0,
  hasConflicts = false,
  synchronizedWithBase = true,
  mergeStrategy = MergeStrategy.SQUASH
}) => {
  if (!Number.isInteger(number) || number <= 0) {
    throw new RangeError('pull-request number must be positive');
  }

  if (!sourceBranch || !targetBranch || sourceBranch === targetBranch) {
    throw new Error('source and target branches must be distinct');
  }

  if (!Array.isArray(commits) || commits.length === 0) {
    throw new Error('a pull request requires at least one commit');
  }

  if (!Number.isInteger(unresolvedConversations) || unresolvedConversations < 0) {
    throw new RangeError('unresolvedConversations must be non-negative');
  }

  return deepFreeze({
    number,
    sourceBranch,
    targetBranch,
    commits: commits.map(commit => ({ ...commit })),
    state,
    reviews: [...reviews],
    checks: [...checks],
    unresolvedConversations,
    hasConflicts: Boolean(hasConflicts),
    synchronizedWithBase: Boolean(synchronizedWithBase),
    mergeStrategy
  });
};

const countApprovals = reviews =>
  reviews.filter(review => review.state === ReviewState.APPROVED).length;

const hasRequestedChanges = reviews =>
  reviews.some(review => review.state === ReviewState.CHANGES_REQUESTED);

const requiredChecksPassed = (checks, policy) => {
  const checkMap = new Map(checks.map(check => [check.name, check.passed]));

  return policy.requiredChecks.every(name => checkMap.get(name) === true);
};

const mergeReasons = (pr, policy) => {
  const reasons = [];

  if (pr.state !== PullRequestState.OPEN) {
    reasons.push('pull request is not open');
  }

  if (pr.commits.length === 0) {
    reasons.push('pull request contains no commits');
  }

  if (pr.sourceBranch === pr.targetBranch) {
    reasons.push('source and target branches are identical');
  }

  if (!pr.synchronizedWithBase) {
    reasons.push('source branch is behind the target branch');
  }

  if (pr.hasConflicts) {
    reasons.push('merge conflicts must be resolved');
  }

  if (hasRequestedChanges(pr.reviews)) {
    reasons.push('a reviewer has requested changes');
  }

  if (countApprovals(pr.reviews) < policy.requiredReviews) {
    reasons.push('required approvals are missing');
  }

  if (!requiredChecksPassed(pr.checks, policy)) {
    reasons.push('required status checks have not passed');
  }

  if (
    policy.requireConversationResolution &&
    pr.unresolvedConversations > 0
  ) {
    reasons.push('review conversations remain unresolved');
  }

  return Object.freeze(reasons);
};

const canMerge = (pr, policy) => mergeReasons(pr, policy).length === 0;

const openDraft = pr => {
  if (pr.state !== PullRequestState.DRAFT) {
    throw new Error('only draft pull requests can be opened');
  }

  return deepFreeze({
    ...pr,
    state: PullRequestState.OPEN
  });
};

const addReview = (pr, review) => {
  if (pr.state !== PullRequestState.OPEN) {
    throw new Error('reviews can only be added to open pull requests');
  }

  return deepFreeze({
    ...pr,
    reviews: [...pr.reviews, review]
  });
};

const updateCheck = (pr, name, passed) => {
  const found = pr.checks.some(check => check.name === name);

  const checks = found
    ? pr.checks.map(check =>
        check.name === name
          ? { ...check, passed: Boolean(passed) }
          : check
      )
    : [...pr.checks, createStatusCheck(name, passed)];

  return deepFreeze({
    ...pr,
    checks
  });
};

const resolveConversation = pr => deepFreeze({
  ...pr,
  unresolvedConversations: Math.max(0, pr.unresolvedConversations - 1)
});

const synchronize = pr => deepFreeze({
  ...pr,
  synchronizedWithBase: true,
  hasConflicts: false
});

const merge = (pr, policy) => {
  const reasons = mergeReasons(pr, policy);

  if (reasons.length > 0) {
    throw new Error(`cannot merge: ${reasons.join('; ')}`);
  }

  return deepFreeze({
    ...pr,
    state: PullRequestState.MERGED
  });
};

const summarize = (pr, policy) => Object.freeze({
  number: pr.number,
  state: pr.state,
  source: pr.sourceBranch,
  target: pr.targetBranch,
  commits: pr.commits.length,
  approvals: countApprovals(pr.reviews),
  requiredApprovals: policy.requiredReviews,
  checksPassed: requiredChecksPassed(pr.checks, policy),
  unresolvedConversations: pr.unresolvedConversations,
  mergeable: canMerge(pr, policy),
  blockingReasons: mergeReasons(pr, policy)
});

const approvalPolicy = policy => pr =>
  countApprovals(pr.reviews) >= policy.requiredReviews;

const checkPolicy = policy => pr =>
  requiredChecksPassed(pr.checks, policy);

const conversationPolicy = policy => pr =>
  !policy.requireConversationResolution ||
  pr.unresolvedConversations === 0;

const allPolicies = policies => pr =>
  policies.every(policy => policy(pr));

const createRepositoryPolicy = policy => allPolicies([
  approvalPolicy(policy),
  checkPolicy(policy),
  conversationPolicy(policy),
  pr => pr.synchronizedWithBase,
  pr => !pr.hasConflicts,
  pr => pr.state === PullRequestState.OPEN,
  pr => !hasRequestedChanges(pr.reviews)
]);

const main = () => {
  const policy = createPolicy({
    requiredReviews: 2,
    requiredChecks: ['unit-tests', 'security-scan'],
    requireConversationResolution: true,
    requireLinearHistory: true,
    allowDirectPush: false,
    allowForcePush: false,
    allowDeletion: false
  });

  const commits = deepFreeze([
    { sha: 'a1b2c3d', message: ' add repository workflow model ' },
    { sha: 'b2c3d4e', message: 'implement merge eligibility' },
    { sha: 'c3d4e5f', message: 'fix' }
  ]);

  const pr = createPullRequest({
    number: 42,
    sourceBranch: 'feature/governance-engine',
    targetBranch: 'main',
    commits,
    unresolvedConversations: 2,
    checks: [
      createStatusCheck('unit-tests', true),
      createStatusCheck('security-scan', false)
    ]
  });

  let current = openDraft(pr);

  current = addReview(
    current,
    createReview({
      reviewer: 'reviewer-alice',
      state: ReviewState.APPROVED,
      comments: ['Policy model is clear.']
    })
  );

  current = addReview(
    current,
    createReview({
      reviewer: 'reviewer-bob',
      state: ReviewState.COMMENTED,
      comments: ['Resolve the policy discussion.']
    })
  );

  console.log('Functional commit pipeline:');
  console.log(functionalCommitPipeline(commits));

  console.log('\nInitial evaluation:');
  console.log(summarize(current, policy));

  current = addReview(
    current,
    createReview({
      reviewer: 'reviewer-bob',
      state: ReviewState.APPROVED
    })
  );

  current = updateCheck(current, 'security-scan', true);
  current = resolveConversation(current);
  current = resolveConversation(current);
  current = synchronize(current);

  const composedEligibility = compose(
    prValue => !prValue.hasConflicts,
    prValue => prValue.synchronizedWithBase,
    prValue => approvalPolicy(policy)(prValue),
    prValue => checkPolicy(policy)(prValue)
  );

  console.log('\nComposed policy evaluation:');
  console.log(composedEligibility(current));

  console.log('\nFinal evaluation:');
  console.log(summarize(current, policy));

  if (canMerge(current, policy)) {
    current = merge(current, policy);
    console.log('\nMerged:', current.state);
  }

  console.log('\nImmutability check:');
  console.log('Original first commit:', commits[0].message);
  console.log('Normalized result:', functionalCommitPipeline(commits)[0]);
};

main();
