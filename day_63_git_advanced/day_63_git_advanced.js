'use strict';

const crypto = require('node:crypto');

class GitError extends Error {}

const CommitType = Object.freeze({
    NORMAL: 'normal',
    MERGE: 'merge',
    REVERT: 'revert'
});

class Commit {
    constructor(hash, message, parents, tree, type = CommitType.NORMAL, metadata = {}) {
        this.hash = hash;
        this.message = message;
        this.parents = [...parents];
        this.tree = new Map(tree);
        this.type = type;
        this.metadata = { ...metadata };
    }
}

class Repository {
    constructor() {
        this.commits = new Map();
        this.branches = new Map();
        this.tags = new Map();
        this.stashes = [];
        this.currentBranch = 'main';
        this.sequence = 0;

        const root = this.createCommit('Initial application', new Map(), []);
        this.branches.set('main', root.hash);
        this.workingTree = new Map(root.tree);
    }

    get head() {
        return this.branches.get(this.currentBranch);
    }

    createCommit(message, tree, parents, type = CommitType.NORMAL, metadata = {}) {
        const hash = crypto
            .createHash('sha1')
            .update(`${++this.sequence}|${message}|${parents.join(',')}|${Date.now()}`)
            .digest('hex')
            .slice(0, 10);

        const commit = new Commit(hash, message, parents, tree, type, metadata);
        this.commits.set(hash, commit);
        return commit;
    }

    checkout(branch) {
        if (!this.branches.has(branch)) throw new GitError(`Unknown branch: ${branch}`);
        this.currentBranch = branch;
        this.workingTree = new Map(this.commits.get(this.head).tree);
    }

    createBranch(name, start = this.head) {
        if (this.branches.has(name)) throw new GitError(`Branch exists: ${name}`);
        if (!this.commits.has(start)) throw new GitError('Invalid starting commit');
        this.branches.set(name, start);
    }

    setFile(path, content) {
        if (!path || path.startsWith('/') || path.includes('\0')) {
            throw new GitError('Invalid repository path');
        }
        this.workingTree.set(path, content);
    }

    removeFile(path) {
        this.workingTree.delete(path);
    }

    status() {
        const committed = this.commits.get(this.head).tree;
        const paths = new Set([...committed.keys(), ...this.workingTree.keys()]);
        const result = new Map();

        for (const path of paths) {
            const oldValue = committed.get(path);
            const newValue = this.workingTree.get(path);
            if (oldValue !== newValue) {
                result.set(path, oldValue === undefined ? 'added'
                    : newValue === undefined ? 'deleted'
                    : 'modified');
            }
        }
        return result;
    }

    commit(message) {
        if (!message.trim()) throw new GitError('Commit message is required');
        if (this.status().size === 0) throw new GitError('Nothing to commit');

        const commit = this.createCommit(
            message,
            this.workingTree,
            [this.head]
        );
        this.branches.set(this.currentBranch, commit.hash);
        return commit.hash;
    }

    ancestors(hash) {
        const result = new Set();
        const stack = [hash];

        while (stack.length) {
            const current = stack.pop();
            if (result.has(current)) continue;
            result.add(current);
            stack.push(...this.commits.get(current).parents);
        }

        return result;
    }

    firstParentChain(hash) {
        const result = [];
        let current = hash;

        while (current) {
            result.push(current);
            const parents = this.commits.get(current).parents;
            current = parents.length ? parents[0] : null;
        }

        return result;
    }

    mergeBase(left, right) {
        const leftAncestors = this.ancestors(left);
        for (const candidate of this.firstParentChain(right)) {
            if (leftAncestors.has(candidate)) return candidate;
        }
        throw new GitError('No merge base');
    }

    merge(sourceBranch) {
        if (!this.branches.has(sourceBranch)) {
            throw new GitError('Unknown source branch');
        }

        const source = this.branches.get(sourceBranch);
        const target = this.head;

        if (source === target) return target;

        if (this.ancestors(source).has(target)) {
            this.branches.set(this.currentBranch, source);
            this.workingTree = new Map(this.commits.get(source).tree);
            return source;
        }

        if (this.ancestors(target).has(source)) return target;

        const base = this.mergeBase(target, source);
        const baseTree = this.commits.get(base).tree;
        const ours = this.commits.get(target).tree;
        const theirs = this.commits.get(source).tree;
        const merged = new Map(ours);
        const paths = new Set([
            ...baseTree.keys(),
            ...ours.keys(),
            ...theirs.keys()
        ]);

        for (const path of paths) {
            const b = baseTree.get(path);
            const o = ours.get(path);
            const t = theirs.get(path);

            if (o === t) {
                if (o === undefined) merged.delete(path);
                else merged.set(path, o);
            } else if (o === b) {
                if (t === undefined) merged.delete(path);
                else merged.set(path, t);
            } else if (t !== b) {
                throw new GitError(`Merge conflict in ${path}`);
            }
        }

        const commit = this.createCommit(
            `Merge ${sourceBranch} into ${this.currentBranch}`,
            merged,
            [target, source],
            CommitType.MERGE
        );

        this.branches.set(this.currentBranch, commit.hash);
        this.workingTree = new Map(merged);
        return commit.hash;
    }

    cherryPick(hash) {
        const source = this.commits.get(hash);
        if (!source || source.parents.length === 0) {
            throw new GitError('Invalid cherry-pick target');
        }

        const parent = this.commits.get(source.parents[0]);
        const current = this.commits.get(this.head).tree;
        const result = new Map(current);

        const paths = new Set([...parent.tree.keys(), ...source.tree.keys()]);

        for (const path of paths) {
            const before = parent.tree.get(path);
            const after = source.tree.get(path);

            if (before === after) continue;

            if (current.get(path) !== before) {
                throw new GitError(`Cherry-pick conflict in ${path}`);
            }

            if (after === undefined) result.delete(path);
            else result.set(path, after);
        }

        const commit = this.createCommit(
            `Cherry-pick: ${source.message}`,
            result,
            [this.head],
            CommitType.NORMAL,
            { 'cherry-picked-from': source.hash }
        );

        this.branches.set(this.currentBranch, commit.hash);
        this.workingTree = new Map(result);
        return commit.hash;
    }

    stashPush(message) {
        if (this.status().size === 0) throw new GitError('No local changes');

        this.stashes.push({
            message,
            tree: new Map(this.workingTree),
            base: this.head
        });

        this.workingTree = new Map(this.commits.get(this.head).tree);
    }

    stashPop() {
        if (!this.stashes.length) throw new GitError('No stash entries');

        const entry = this.stashes[this.stashes.length - 1];
        const currentTree = this.commits.get(this.head).tree;
        const baseTree = this.commits.get(entry.base).tree;

        if (!mapsEqual(currentTree, baseTree)) {
            throw new GitError('Stash application requires conflict resolution');
        }

        this.workingTree = new Map(entry.tree);
        this.stashes.pop();
    }

    reset(target, mode = 'mixed') {
        if (!this.commits.has(target)) throw new GitError('Unknown reset target');
        if (!['soft', 'mixed', 'hard'].includes(mode)) {
            throw new GitError('Invalid reset mode');
        }

        const oldWorkingTree = new Map(this.workingTree);
        this.branches.set(this.currentBranch, target);

        if (mode !== 'soft') {
            this.workingTree = new Map(this.commits.get(target).tree);
        } else {
            this.workingTree = oldWorkingTree;
        }
    }

    revert(targetHash) {
        const target = this.commits.get(targetHash);
        if (!target || target.parents.length === 0) {
            throw new GitError('Cannot revert this commit');
        }

        const parent = this.commits.get(target.parents[0]);
        const current = this.commits.get(this.head).tree;
        const result = new Map(current);

        const paths = new Set([...parent.tree.keys(), ...target.tree.keys()]);

        for (const path of paths) {
            const before = parent.tree.get(path);
            const after = target.tree.get(path);

            if (before === after) continue;

            if (current.get(path) !== after) {
                throw new GitError(`Revert conflict in ${path}`);
            }

            if (before === undefined) result.delete(path);
            else result.set(path, before);
        }

        const commit = this.createCommit(
            `Revert: ${target.message}`,
            result,
            [this.head],
            CommitType.REVERT,
            { reverts: target.hash }
        );

        this.branches.set(this.currentBranch, commit.hash);
        this.workingTree = new Map(result);
        return commit.hash;
    }

    tag(name, target = this.head) {
        if (!/^[A-Za-z0-9._/-]+$/.test(name) || name.startsWith('-')) {
            throw new GitError('Invalid tag name');
        }
        if (this.tags.has(name)) throw new GitError('Tag already exists');
        if (!this.commits.has(target)) throw new GitError('Unknown tag target');
        this.tags.set(name, target);
    }

    log() {
        return this.firstParentChain(this.head)
            .map(hash => `${hash} ${this.commits.get(hash).message}`);
    }
}

function mapsEqual(a, b) {
    if (a.size !== b.size) return false;
    for (const [key, value] of a) {
        if (b.get(key) !== value) return false;
    }
    return true;
}

async function main() {
    const repo = new Repository();

    repo.setFile('app.js', 'console.log("v1");\n');
    const baseCommit = repo.commit('Add application entry point');

    repo.createBranch('feature/cache');
    repo.checkout('feature/cache');
    repo.setFile('cache.js', 'const CACHE_SIZE = 256;\n');
    const featureCommit = repo.commit('Add cache configuration');

    repo.setFile('cache.js', 'const CACHE_SIZE = 512;\n');
    repo.commit('Tune cache size');

    repo.checkout('main');
    repo.setFile('README.md', '# Deployment\n');
    repo.commit('Document deployment');

    repo.merge('feature/cache');

    repo.createBranch('maintenance');
    repo.checkout('maintenance');
    repo.cherryPick(baseCommit);

    repo.setFile('local.env', 'TIMEOUT=30\n');
    repo.stashPush('Temporary local configuration');
    repo.stashPop();

    const revertTarget = repo.head;
    repo.revert(revertTarget);
    repo.tag('v1.0.0');

    console.log('=== Git Advanced Workflow ===');
    console.log('Branch:', repo.currentBranch);
    console.log('HEAD:', repo.head);
    console.log('Tags:', Object.fromEntries(repo.tags));
    console.log('Status:', Object.fromEntries(repo.status()));
    console.log('Log:');
    repo.log().forEach(line => console.log(`  ${line}`));

    if (!repo.tags.has('v1.0.0') || repo.stashes.length !== 0) {
        throw new GitError('Workflow invariant failed');
    }

    void featureCommit;
}

main().catch(error => {
    console.error(`Git workflow failed: ${error.message}`);
    process.exitCode = 1;
});
