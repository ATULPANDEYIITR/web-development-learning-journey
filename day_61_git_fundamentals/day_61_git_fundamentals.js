'use strict';

const crypto = require('node:crypto');
const fs = require('node:fs/promises');
const os = require('node:os');
const path = require('node:path');

class GitError extends Error {}
class ValidationError extends GitError {}
class RepositoryStateError extends GitError {}
class BranchNotFoundError extends GitError {}
class CommitNotFoundError extends GitError {}

const ObjectType = Object.freeze({
    BLOB: 'blob',
    TREE: 'tree',
    COMMIT: 'commit'
});

class Repository {
    constructor() {
        this.workingTree = new Map();
        this.index = new Map();
        this.objects = new Map();
        this.commits = new Map();
        this.branches = new Map([['main', '']]);
        this.headBranch = 'main';
        this.detachedHead = null;
    }

    get head() {
        return this.detachedHead ?? this.branches.get(this.headBranch) ?? null;
    }

    validatePath(filePath) {
        if (
            !filePath ||
            path.posix.isAbsolute(filePath) ||
            filePath.split('/').includes('..')
        ) {
            throw new ValidationError(`Unsafe repository path: ${filePath}`);
        }
    }

    validateBranchName(name) {
        if (!/^[A-Za-z0-9._/-]+$/.test(name) || name.startsWith('/') ||
            name.endsWith('/') || name.includes('..')) {
            throw new ValidationError(`Invalid branch name: ${name}`);
        }
    }

    writeFile(filePath, content) {
        this.validatePath(filePath);
        if (typeof content !== 'string') {
            throw new ValidationError('File content must be a string.');
        }
        this.workingTree.set(filePath, content);
    }

    deleteFile(filePath) {
        this.validatePath(filePath);
        if (!this.workingTree.has(filePath)) {
            throw new GitError(`File does not exist: ${filePath}`);
        }
        this.workingTree.delete(filePath);
    }

    add(paths) {
        for (const filePath of paths) {
            this.validatePath(filePath);
            if (!this.workingTree.has(filePath)) {
                throw new GitError(`File does not exist: ${filePath}`);
            }
            this.index.set(filePath, this.workingTree.get(filePath));
        }
    }

    addAll() {
        this.index = new Map(this.workingTree);
    }

    status() {
        const committed = this.head
            ? this.commits.get(this.head).tree
            : new Map();

        const staged = [];
        const modified = [];
        const untracked = [];

        const allTracked = new Set([...committed.keys(), ...this.index.keys()]);
        for (const filePath of [...allTracked].sort()) {
            if (committed.get(filePath) !== this.index.get(filePath)) {
                staged.push(filePath);
            }
        }

        const allWorking = new Set([...this.index.keys(), ...this.workingTree.keys()]);
        for (const filePath of [...allWorking].sort()) {
            if (this.index.get(filePath) !== this.workingTree.get(filePath)) {
                modified.push(filePath);
            }
        }

        for (const filePath of [...this.workingTree.keys()].sort()) {
            if (!committed.has(filePath) && !this.index.has(filePath)) {
                untracked.push(filePath);
            }
        }

        return { staged, modified, untracked };
    }

    hasUncommittedChanges() {
        const state = this.status();
        return state.staged.length > 0 ||
            state.modified.length > 0 ||
            state.untracked.length > 0;
    }

    createObject(type, content) {
        const body = Buffer.from(content, 'utf8');
        const header = Buffer.from(`${type} ${body.length}\0`, 'utf8');
        const objectId = crypto
            .createHash('sha1')
            .update(Buffer.concat([header, body]))
            .digest('hex');

        if (!this.objects.has(objectId)) {
            this.objects.set(objectId, { type, content });
        }
        return objectId;
    }

    commit(message, author) {
        message = message.trim();
        author = author.trim();

        if (!message) throw new ValidationError('Commit message is required.');
        if (!author) throw new ValidationError('Commit author is required.');
        if (this.index.size === 0) {
            throw new RepositoryStateError('Nothing is staged.');
        }

        for (const [filePath, content] of this.index) {
            this.createObject(ObjectType.BLOB, content);
        }

        const tree = new Map(this.index);
        const payload = JSON.stringify({
            author,
            message,
            parents: this.head ? [this.head] : [],
            tree: [...tree.entries()].sort()
        });

        const commitId = this.createObject(ObjectType.COMMIT, payload);

        this.commits.set(commitId, {
            id: commitId,
            author,
            message,
            parents: this.head ? [this.head] : [],
            tree
        });

        if (this.detachedHead) {
            this.detachedHead = commitId;
        } else {
            this.branches.set(this.headBranch, commitId);
        }

        this.index = new Map(tree);
        return commitId;
    }

    createBranch(name, startPoint = this.head) {
        this.validateBranchName(name);
        if (this.branches.has(name)) {
            throw new ValidationError(`Branch exists: ${name}`);
        }
        if (startPoint && !this.commits.has(startPoint)) {
            throw new CommitNotFoundError(startPoint);
        }
        this.branches.set(name, startPoint ?? '');
    }

    checkout(target) {
        if (this.hasUncommittedChanges()) {
            throw new RepositoryStateError(
                'Commit or clean local changes before checkout.'
            );
        }

        if (this.branches.has(target)) {
            this.detachedHead = null;
            this.headBranch = target;
            this.restoreTree(this.branches.get(target));
            return;
        }

        if (!this.commits.has(target)) {
            throw new CommitNotFoundError(target);
        }

        this.detachedHead = target;
        this.restoreTree(target);
    }

    restoreTree(commitId) {
        const tree = commitId ? this.commits.get(commitId).tree : new Map();
        this.workingTree = new Map(tree);
        this.index = new Map(tree);
    }

    ancestors(start) {
        const distances = new Map([[start, 0]]);
        const queue = [start];

        while (queue.length) {
            const current = queue.shift();
            const commit = this.commits.get(current);
            for (const parent of commit.parents) {
                if (!distances.has(parent)) {
                    distances.set(parent, distances.get(current) + 1);
                    queue.push(parent);
                }
            }
        }

        return distances;
    }

    isAncestor(ancestor, descendant) {
        return this.ancestors(descendant).has(ancestor);
    }

    mergeBase(left, right) {
        const a = this.ancestors(left);
        const b = this.ancestors(right);
        let best = null;
        let bestDistance = Infinity;

        for (const [id, distance] of a) {
            if (b.has(id)) {
                const total = distance + b.get(id);
                if (total < bestDistance) {
                    best = id;
                    bestDistance = total;
                }
            }
        }
        return best;
    }

    merge(sourceBranch) {
        if (this.detachedHead) {
            throw new RepositoryStateError('Cannot merge from detached HEAD.');
        }
        if (!this.branches.has(sourceBranch)) {
            throw new BranchNotFoundError(sourceBranch);
        }
        if (this.hasUncommittedChanges()) {
            throw new RepositoryStateError('Working tree must be clean.');
        }

        const ours = this.head;
        const theirs = this.branches.get(sourceBranch);

        if (!theirs) throw new RepositoryStateError('Source branch is empty.');
        if (!ours) {
            this.branches.set(this.headBranch, theirs);
            this.restoreTree(theirs);
            return theirs;
        }
        if (ours === theirs || this.isAncestor(theirs, ours)) return ours;

        if (this.isAncestor(ours, theirs)) {
            this.branches.set(this.headBranch, theirs);
            this.restoreTree(theirs);
            return theirs;
        }

        const base = this.mergeBase(ours, theirs);
        if (!base) throw new RepositoryStateError('No merge base found.');

        const baseTree = this.commits.get(base).tree;
        const ourTree = this.commits.get(ours).tree;
        const theirTree = this.commits.get(theirs).tree;
        const merged = new Map();
        const conflicts = [];

        const files = new Set([
            ...baseTree.keys(),
            ...ourTree.keys(),
            ...theirTree.keys()
        ]);

        for (const filePath of [...files].sort()) {
            const baseValue = baseTree.get(filePath);
            const ourValue = ourTree.get(filePath);
            const theirValue = theirTree.get(filePath);

            if (ourValue === theirValue) {
                if (ourValue !== undefined) merged.set(filePath, ourValue);
            } else if (ourValue === baseValue) {
                if (theirValue !== undefined) merged.set(filePath, theirValue);
            } else if (theirValue === baseValue) {
                if (ourValue !== undefined) merged.set(filePath, ourValue);
            } else {
                conflicts.push(filePath);
            }
        }

        if (conflicts.length) {
            throw new RepositoryStateError(
                `Merge conflicts: ${conflicts.join(', ')}`
            );
        }

        this.workingTree = new Map(merged);
        this.index = new Map(merged);
        return this.commit(
            `Merge branch '${sourceBranch}' into ${this.headBranch}`,
            'merge-bot'
        );
    }

    async saveSnapshot() {
        const directory = await fs.mkdtemp(
            path.join(os.tmpdir(), 'git-model-')
        );

        const serializeMap = map => Object.fromEntries(map);

        await fs.writeFile(
            path.join(directory, 'working-tree.json'),
            JSON.stringify(serializeMap(this.workingTree), null, 2)
        );
        await fs.writeFile(
            path.join(directory, 'index.json'),
            JSON.stringify(serializeMap(this.index), null, 2)
        );
        await fs.writeFile(
            path.join(directory, 'refs.json'),
            JSON.stringify({
                headBranch: this.headBranch,
                detachedHead: this.detachedHead,
                branches: Object.fromEntries(this.branches)
            }, null, 2)
        );

        return directory;
    }

    async auditAsync() {
        return new Promise(resolve => {
            setImmediate(() => {
                resolve({
                    head: this.head,
                    branch: this.detachedHead ? null : this.headBranch,
                    objectCount: this.objects.size,
                    commitCount: this.commits.size,
                    clean: !this.hasUncommittedChanges()
                });
            });
        });
    }
}

function printStatus(repo) {
    console.log('\nSTATUS');
    console.log(JSON.stringify(repo.status(), null, 2));
}

async function main() {
    const repo = new Repository();

    repo.writeFile('README.md', '# Repository\n');
    repo.writeFile('server.js', 'console.log("v1");\n');
    repo.addAll();

    const initial = repo.commit(
        'Initialize repository',
        'developer@example.com'
    );

    repo.writeFile('server.js', 'console.log("v2");\n');
    repo.writeFile('debug.log', 'local diagnostic data\n');
    printStatus(repo);

    repo.add(['server.js']);
    repo.createBranch('feature/audit');
    repo.checkout('feature/audit');

    repo.writeFile('audit.json', '{"enabled":true}\n');
    repo.add(['audit.json']);
    const feature = repo.commit(
        'Add audit configuration',
        'security@example.com'
    );

    repo.checkout('main');
    repo.writeFile('README.md', '# Repository\nGit workflow model\n');
    repo.add(['README.md']);
    repo.commit(
        'Document repository state',
        'developer@example.com'
    );

    const merge = repo.merge('feature/audit');

    console.log('\nBRANCHES');
    for (const [name, commitId] of repo.branches) {
        console.log(`${name.padEnd(16)} ${commitId.slice(0, 12) || '(empty)'}`);
    }

    console.log('\nOBJECTS');
    console.log(repo.objects.size);

    console.log('\nCOMMIT RELATIONSHIPS');
    console.log(`initial: ${initial.slice(0, 12)}`);
    console.log(`feature: ${feature.slice(0, 12)}`);
    console.log(`merge:   ${merge.slice(0, 12)}`);

    const audit = await repo.auditAsync();
    console.log('\nASYNC AUDIT');
    console.log(audit);

    const snapshot = await repo.saveSnapshot();
    console.log(`\nSnapshot: ${snapshot}`);

    repo.checkout(initial);
    console.log(`\nDetached HEAD: ${repo.head.slice(0, 12)}`);

    repo.checkout('main');
    console.log(`Attached HEAD: ${repo.head.slice(0, 12)}`);

    try {
        repo.writeFile('../outside.txt', 'blocked');
    } catch (error) {
        if (!(error instanceof ValidationError)) throw error;
        console.log('\nUnsafe path rejected.');
    }

    console.log('\nRepository model validated.');
}

main().catch(error => {
    console.error(`Fatal error: ${error.message}`);
    process.exitCode = 1;
});
