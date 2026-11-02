import java.util.*;
import java.util.function.Predicate;
import java.util.stream.Collectors;

public class GitAdvancedWorkflow {

    enum CommitType {
        NORMAL, MERGE, REVERT
    }

    enum ResetMode {
        SOFT, MIXED, HARD
    }

    record Commit(
        String id,
        String message,
        List<String> parents,
        Map<String, String> tree,
        CommitType type,
        Map<String, String> metadata
    ) {
        Commit {
            parents = List.copyOf(parents);
            tree = Map.copyOf(tree);
            metadata = Map.copyOf(metadata);
        }
    }

    record StashEntry(
        String message,
        Map<String, String> tree,
        String baseCommit
    ) {
        StashEntry {
            tree = Map.copyOf(tree);
        }
    }

    static class GitException extends RuntimeException {
        GitException(String message) {
            super(message);
        }
    }

    interface RepositoryPolicy {
        void validateBranchName(String branch);
        void validateCommitMessage(String message);
        void validateTagName(String tag);
    }

    static final class DefaultRepositoryPolicy implements RepositoryPolicy {
        @Override
        public void validateBranchName(String branch) {
            if (branch == null || branch.isBlank() || branch.contains(" ")) {
                throw new GitException("Invalid branch name");
            }
        }

        @Override
        public void validateCommitMessage(String message) {
            if (message == null || message.isBlank()) {
                throw new GitException("Commit message is required");
            }
        }

        @Override
        public void validateTagName(String tag) {
            if (tag == null || tag.isBlank() || tag.startsWith("-") || tag.contains(" ")) {
                throw new GitException("Invalid tag name");
            }
        }
    }

    static final class RepositoryService {
        private final Map<String, Commit> commits = new LinkedHashMap<>();
        private final Map<String, String> branches = new LinkedHashMap<>();
        private final Map<String, String> tags = new LinkedHashMap<>();
        private final Deque<StashEntry> stashes = new ArrayDeque<>();
        private final RepositoryPolicy policy = new DefaultRepositoryPolicy();

        private String currentBranch = "main";
        private long sequence;

        RepositoryService() {
            Commit root = createCommit(
                "Initial application",
                Map.of(),
                List.of(),
                CommitType.NORMAL,
                Map.of()
            );

            branches.put("main", root.id());
        }

        String head() {
            return branches.get(currentBranch);
        }

        Map<String, String> workingTree() {
            return new LinkedHashMap<>(commits.get(head()).tree());
        }

        void checkout(String branch) {
            if (!branches.containsKey(branch)) {
                throw new GitException("Unknown branch: " + branch);
            }
            currentBranch = branch;
        }

        void createBranch(String branch) {
            policy.validateBranchName(branch);
            if (branches.containsKey(branch)) {
                throw new GitException("Branch already exists");
            }
            branches.put(branch, head());
        }

        Commit createCommit(
            String message,
            Map<String, String> tree,
            List<String> parents,
            CommitType type,
            Map<String, String> metadata
        ) {
            policy.validateCommitMessage(message);

            String id = Integer.toHexString(
                Objects.hash(++sequence, message, parents, tree)
            );

            Commit commit = new Commit(
                id,
                message,
                parents,
                tree,
                type,
                metadata
            );

            commits.put(id, commit);
            return commit;
        }

        String commit(String message, Map<String, String> newTree) {
            if (newTree.equals(commits.get(head()).tree())) {
                throw new GitException("Nothing to commit");
            }

            Commit commit = createCommit(
                message,
                newTree,
                List.of(head()),
                CommitType.NORMAL,
                Map.of()
            );

            branches.put(currentBranch, commit.id());
            return commit.id();
        }

        Set<String> ancestors(String id) {
            Set<String> result = new LinkedHashSet<>();
            Deque<String> queue = new ArrayDeque<>();
            queue.add(id);

            while (!queue.isEmpty()) {
                String current = queue.removeFirst();
                if (!result.add(current)) continue;
                queue.addAll(commits.get(current).parents());
            }

            return result;
        }

        List<String> firstParentChain(String id) {
            List<String> result = new ArrayList<>();
            String current = id;

            while (current != null && !current.isEmpty()) {
                result.add(current);
                List<String> parents = commits.get(current).parents();
                current = parents.isEmpty() ? null : parents.getFirst();
            }

            return result;
        }

        String mergeBase(String left, String right) {
            Set<String> leftAncestors = ancestors(left);

            return firstParentChain(right).stream()
                .filter(leftAncestors::contains)
                .findFirst()
                .orElseThrow(() -> new GitException("No merge base"));
        }

        String merge(String sourceBranch) {
            if (!branches.containsKey(sourceBranch)) {
                throw new GitException("Unknown source branch");
            }

            String source = branches.get(sourceBranch);
            String target = head();

            if (source.equals(target)) return target;

            if (ancestors(source).contains(target)) {
                branches.put(currentBranch, source);
                return source;
            }

            if (ancestors(target).contains(source)) return target;

            String base = mergeBase(target, source);
            Map<String, String> baseTree = commits.get(base).tree();
            Map<String, String> ours = commits.get(target).tree();
            Map<String, String> theirs = commits.get(source).tree();
            Map<String, String> merged = new LinkedHashMap<>(ours);

            Set<String> paths = new HashSet<>();
            paths.addAll(baseTree.keySet());
            paths.addAll(ours.keySet());
            paths.addAll(theirs.keySet());

            for (String path : paths) {
                String b = baseTree.get(path);
                String o = ours.get(path);
                String t = theirs.get(path);

                if (Objects.equals(o, t)) {
                    if (o == null) merged.remove(path);
                    else merged.put(path, o);
                } else if (Objects.equals(o, b)) {
                    if (t == null) merged.remove(path);
                    else merged.put(path, t);
                } else if (!Objects.equals(t, b)) {
                    throw new GitException("Merge conflict in " + path);
                }
            }

            Commit mergeCommit = createCommit(
                "Merge " + sourceBranch + " into " + currentBranch,
                merged,
                List.of(target, source),
                CommitType.MERGE,
                Map.of()
            );

            branches.put(currentBranch, mergeCommit.id());
            return mergeCommit.id();
        }

        String cherryPick(String sourceId) {
            Commit source = requireCommit(sourceId);

            if (source.parents().isEmpty()) {
                throw new GitException("Cannot cherry-pick root commit");
            }

            Commit parent = requireCommit(source.parents().getFirst());
            Map<String, String> current = workingTree();
            Map<String, String> result = new LinkedHashMap<>(current);

            Set<String> paths = new HashSet<>();
            paths.addAll(parent.tree().keySet());
            paths.addAll(source.tree().keySet());

            for (String path : paths) {
                String before = parent.tree().get(path);
                String after = source.tree().get(path);

                if (Objects.equals(before, after)) continue;

                if (!Objects.equals(current.get(path), before)) {
                    throw new GitException("Cherry-pick conflict in " + path);
                }

                if (after == null) result.remove(path);
                else result.put(path, after);
            }

            Commit newCommit = createCommit(
                "Cherry-pick: " + source.message(),
                result,
                List.of(head()),
                CommitType.NORMAL,
                Map.of("cherry-picked-from", source.id())
            );

            branches.put(currentBranch, newCommit.id());
            return newCommit.id();
        }

        void stash(Map<String, String> workingTree, String message) {
            if (workingTree.equals(commits.get(head()).tree())) {
                throw new GitException("No local changes to stash");
            }

            stashes.push(new StashEntry(message, workingTree, head()));
        }

        Map<String, String> stashPop() {
            if (stashes.isEmpty()) {
                throw new GitException("No stash entries");
            }

            StashEntry entry = stashes.peek();
            if (!commits.get(head()).tree().equals(commits.get(entry.baseCommit()).tree())) {
                throw new GitException("Stash cannot be applied cleanly");
            }

            stashes.pop();
            return new LinkedHashMap<>(entry.tree());
        }

        void reset(String target, ResetMode mode, Map<String, String> currentWorkingTree) {
            requireCommit(target);

            if (mode == ResetMode.SOFT) {
                branches.put(currentBranch, target);
            } else {
                branches.put(currentBranch, target);
                currentWorkingTree.clear();
                currentWorkingTree.putAll(commits.get(target).tree());
            }
        }

        String revert(String targetId) {
            Commit target = requireCommit(targetId);

            if (target.parents().isEmpty()) {
                throw new GitException("Cannot revert root commit");
            }

            Commit parent = requireCommit(target.parents().getFirst());
            Map<String, String> current = workingTree();
            Map<String, String> result = new LinkedHashMap<>(current);

            Set<String> paths = new HashSet<>();
            paths.addAll(parent.tree().keySet());
            paths.addAll(target.tree().keySet());

            for (String path : paths) {
                String before = parent.tree().get(path);
                String after = target.tree().get(path);

                if (Objects.equals(before, after)) continue;

                if (!Objects.equals(current.get(path), after)) {
                    throw new GitException("Revert conflict in " + path);
                }

                if (before == null) result.remove(path);
                else result.put(path, before);
            }

            Commit revert = createCommit(
                "Revert: " + target.message(),
                result,
                List.of(head()),
                CommitType.REVERT,
                Map.of("reverts", target.id())
            );

            branches.put(currentBranch, revert.id());
            return revert.id();
        }

        void tag(String name, String target) {
            policy.validateTagName(name);
            requireCommit(target);

            if (tags.containsKey(name)) {
                throw new GitException("Tag already exists");
            }

            tags.put(name, target);
        }

        Commit requireCommit(String id) {
            Commit commit = commits.get(id);
            if (commit == null) throw new GitException("Unknown commit");
            return commit;
        }

        void printHistory() {
            firstParentChain(head()).forEach(id -> {
                Commit c = commits.get(id);
                System.out.println("  " + id + " " + c.message());
            });
        }

        Map<String, String> tags() {
            return Map.copyOf(tags);
        }
    }

    public static void main(String[] args) {
        try {
            RepositoryService repository = new RepositoryService();

            Map<String, String> mainTree = repository.workingTree();
            mainTree.put("application.properties", "version=1\n");
            String initialFeature = repository.commit(
                "Add application configuration",
                mainTree
            );

            repository.createBranch("feature/cache");
            repository.checkout("feature/cache");

            Map<String, String> featureTree = repository.workingTree();
            featureTree.put("cache.properties", "size=256\n");
            repository.commit("Add cache configuration", featureTree);

            featureTree = repository.workingTree();
            featureTree.put("cache.properties", "size=512\n");
            repository.commit("Tune cache size", featureTree);

            repository.checkout("main");
            Map<String, String> mainUpdate = repository.workingTree();
            mainUpdate.put("README.md", "# Deployment Guide\n");
            repository.commit("Document deployment", mainUpdate);

            repository.merge("feature/cache");

            repository.createBranch("maintenance");
            repository.checkout("maintenance");
            repository.cherryPick(initialFeature);

            Map<String, String> localChanges = repository.workingTree();
            localChanges.put("local.conf", "timeout=30\n");
            repository.stash(localChanges, "Temporary local configuration");

            Map<String, String> restored = repository.stashPop();
            restored.put("local.conf", "timeout=60\n");

            String revertTarget = repository.head();
            repository.revert(revertTarget);
            repository.tag("v1.0.0", repository.head());

            System.out.println("=== Enterprise Git Workflow ===");
            System.out.println("Branch: " + repository.currentBranch);
            System.out.println("HEAD: " + repository.head());
            System.out.println("Tags: " + repository.tags());
            System.out.println("History:");
            repository.printHistory();

            Predicate<String> validTag = tag -> repository.tags().containsKey(tag);
            if (!validTag.test("v1.0.0")) {
                throw new GitException("Release tag invariant failed");
            }

            System.out.println("Workflow completed successfully.");
        } catch (GitException ex) {
            System.err.println("Git workflow error: " + ex.getMessage());
            System.exit(1);
        }
    }
}
