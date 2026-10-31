import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Collections;
import java.util.EnumMap;
import java.util.HashMap;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Queue;
import java.util.Set;
import java.util.regex.Pattern;

public class GitFundamentalsEnterprise {

    enum ObjectType {
        BLOB, TREE, COMMIT
    }

    enum FileState {
        STAGED, MODIFIED, UNTRACKED
    }

    enum RepositoryState {
        ACTIVE, MERGING
    }

    record GitObject(ObjectType type, String content, String id) {}

    record Commit(
            String id,
            String message,
            String author,
            List<String> parents,
            Map<String, String> tree
    ) {
        Commit {
            parents = List.copyOf(parents);
            tree = Map.copyOf(tree);
        }
    }

    record Branch(String name, String commitId) {}

    record ReviewPolicy(
            int requiredApprovals,
            Set<String> requiredChecks,
            boolean requireCleanTree
    ) {
        ReviewPolicy {
            if (requiredApprovals < 0) {
                throw new IllegalArgumentException(
                        "Approval count cannot be negative."
                );
            }
            requiredChecks = Set.copyOf(requiredChecks);
        }
    }

    static class GitException extends RuntimeException {
        GitException(String message) {
            super(message);
        }
    }

    static class ValidationException extends GitException {
        ValidationException(String message) {
            super(message);
        }
    }

    static class StateException extends GitException {
        StateException(String message) {
            super(message);
        }
    }

    static class Repository {
        private static final Pattern SAFE_BRANCH =
                Pattern.compile("[A-Za-z0-9._/-]+");

        private final Map<String, String> workingTree = new LinkedHashMap<>();
        private final Map<String, String> index = new LinkedHashMap<>();
        private final Map<String, GitObject> objects = new HashMap<>();
        private final Map<String, Commit> commits = new HashMap<>();
        private final Map<String, Branch> branches = new LinkedHashMap<>();

        private String headBranch = "main";
        private String detachedHead;
        private RepositoryState state = RepositoryState.ACTIVE;

        Repository() {
            branches.put("main", new Branch("main", ""));
        }

        String head() {
            if (detachedHead != null) {
                return detachedHead;
            }

            return branches.get(headBranch).commitId();
        }

        void writeFile(String file, String content) {
            validatePath(file);
            Objects.requireNonNull(content, "content");
            workingTree.put(file, content);
        }

        void addAll() {
            index.clear();
            index.putAll(workingTree);
        }

        void add(String... files) {
            for (String file : files) {
                validatePath(file);
                if (!workingTree.containsKey(file)) {
                    throw new ValidationException(
                            "File does not exist: " + file
                    );
                }
                index.put(file, workingTree.get(file));
            }
        }

        EnumMap<FileState, List<String>> status() {
            EnumMap<FileState, List<String>> result =
                    new EnumMap<>(FileState.class);

            Map<String, String> committed =
                    head().isBlank()
                            ? Map.of()
                            : commits.get(head()).tree();

            Set<String> files = new HashSet<>();
            files.addAll(committed.keySet());
            files.addAll(index.keySet());
            files.addAll(workingTree.keySet());

            List<String> sorted = new ArrayList<>(files);
            Collections.sort(sorted);

            for (String file : sorted) {
                String oldValue = committed.get(file);
                String stagedValue = index.get(file);
                String workingValue = workingTree.get(file);

                if (!Objects.equals(oldValue, stagedValue)) {
                    result.computeIfAbsent(
                            FileState.STAGED,
                            ignored -> new ArrayList<>()
                    ).add(file);
                }

                if (!Objects.equals(stagedValue, workingValue)
                        && workingTree.containsKey(file)) {
                    result.computeIfAbsent(
                            FileState.MODIFIED,
                            ignored -> new ArrayList<>()
                    ).add(file);
                }

                if (!committed.containsKey(file)
                        && !index.containsKey(file)
                        && workingTree.containsKey(file)) {
                    result.computeIfAbsent(
                            FileState.UNTRACKED,
                            ignored -> new ArrayList<>()
                    ).add(file);
                }
            }

            return result;
        }

        boolean isClean() {
            return status().isEmpty();
        }

        String commit(String message, String author) {
            if (message == null || message.isBlank()) {
                throw new ValidationException(
                        "Commit message is required."
                );
            }

            if (author == null || author.isBlank()) {
                throw new ValidationException(
                        "Commit author is required."
                );
            }

            if (index.isEmpty()) {
                throw new StateException("Nothing is staged.");
            }

            String parent = head();

            for (Map.Entry<String, String> entry : index.entrySet()) {
                String blobId = stableId(
                        "blob:" + entry.getKey() + ":" + entry.getValue()
                );

                objects.putIfAbsent(
                        blobId,
                        new GitObject(
                                ObjectType.BLOB,
                                entry.getValue(),
                                blobId
                        )
                );
            }

            StringBuilder payload = new StringBuilder()
                    .append(author)
                    .append('\n')
                    .append(message)
                    .append('\n')
                    .append(parent)
                    .append('\n');

            index.entrySet().stream()
                    .sorted(Map.Entry.comparingByKey())
                    .forEach(entry ->
                            payload.append(entry.getKey())
                                    .append('=')
                                    .append(entry.getValue())
                                    .append('\n')
                    );

            String id = stableId("commit:" + payload);

            List<String> parents =
                    parent.isBlank()
                            ? List.of()
                            : List.of(parent);

            Commit commit = new Commit(
                    id,
                    message,
                    author,
                    parents,
                    index
            );

            commits.put(id, commit);
            objects.put(
                    id,
                    new GitObject(
                            ObjectType.COMMIT,
                            payload.toString(),
                            id
                    )
            );

            if (detachedHead != null) {
                detachedHead = id;
            } else {
                branches.put(
                        headBranch,
                        new Branch(headBranch, id)
                );
            }

            return id;
        }

        void createBranch(String name) {
            validateBranch(name);

            if (branches.containsKey(name)) {
                throw new ValidationException(
                        "Branch already exists: " + name
                );
            }

            branches.put(
                    name,
                    new Branch(name, head())
            );
        }

        void checkout(String target) {
            if (!isClean()) {
                throw new StateException(
                        "Cannot checkout with uncommitted changes."
                );
            }

            if (branches.containsKey(target)) {
                detachedHead = null;
                headBranch = target;
                restoreTree(branches.get(target).commitId());
                return;
            }

            if (!commits.containsKey(target)) {
                throw new ValidationException(
                        "Unknown branch or commit: " + target
                );
            }

            detachedHead = target;
            restoreTree(target);
        }

        private void restoreTree(String commitId) {
            workingTree.clear();
            index.clear();

            if (commitId.isBlank()) {
                return;
            }

            Map<String, String> tree = commits.get(commitId).tree();
            workingTree.putAll(tree);
            index.putAll(tree);
        }

        boolean isAncestor(String ancestor, String descendant) {
            Queue<String> queue = new ArrayDeque<>();
            Set<String> visited = new HashSet<>();
            queue.add(descendant);

            while (!queue.isEmpty()) {
                String current = queue.remove();

                if (!visited.add(current)) {
                    continue;
                }

                if (current.equals(ancestor)) {
                    return true;
                }

                queue.addAll(commits.get(current).parents());
            }

            return false;
        }

        String mergeBase(String left, String right) {
            Map<String, Integer> leftDistances =
                    ancestorDistances(left);
            Map<String, Integer> rightDistances =
                    ancestorDistances(right);

            String best = null;
            int bestDistance = Integer.MAX_VALUE;

            for (Map.Entry<String, Integer> entry
                    : leftDistances.entrySet()) {

                Integer rightDistance = rightDistances.get(entry.getKey());

                if (rightDistance != null) {
                    int distance = entry.getValue() + rightDistance;

                    if (distance < bestDistance) {
                        best = entry.getKey();
                        bestDistance = distance;
                    }
                }
            }

            return best;
        }

        private Map<String, Integer> ancestorDistances(String start) {
            Map<String, Integer> distance = new HashMap<>();
            Queue<String> queue = new ArrayDeque<>();

            distance.put(start, 0);
            queue.add(start);

            while (!queue.isEmpty()) {
                String current = queue.remove();
                int currentDistance = distance.get(current);

                for (String parent : commits.get(current).parents()) {
                    if (!distance.containsKey(parent)) {
                        distance.put(parent, currentDistance + 1);
                        queue.add(parent);
                    }
                }
            }

            return distance;
        }

        String merge(String sourceBranch) {
            if (detachedHead != null) {
                throw new StateException(
                        "Merge requires an attached HEAD."
                );
            }

            if (!branches.containsKey(sourceBranch)) {
                throw new ValidationException(
                        "Source branch does not exist."
                );
            }

            if (!isClean()) {
                throw new StateException(
                        "Working tree must be clean."
                );
            }

            String ours = head();
            String theirs = branches.get(sourceBranch).commitId();

            if (theirs.isBlank()) {
                throw new StateException(
                        "Source branch has no commits."
                );
            }

            if (ours.isBlank()) {
                branches.put(
                        headBranch,
                        new Branch(headBranch, theirs)
                );
                restoreTree(theirs);
                return theirs;
            }

            if (ours.equals(theirs)
                    || isAncestor(theirs, ours)) {
                return ours;
            }

            if (isAncestor(ours, theirs)) {
                branches.put(
                        headBranch,
                        new Branch(headBranch, theirs)
                );
                restoreTree(theirs);
                return theirs;
            }

            String base = mergeBase(ours, theirs);

            if (base == null) {
                throw new StateException("No merge base found.");
            }

            Map<String, String> baseTree =
                    commits.get(base).tree();
            Map<String, String> ourTree =
                    commits.get(ours).tree();
            Map<String, String> theirTree =
                    commits.get(theirs).tree();

            Set<String> files = new HashSet<>();
            files.addAll(baseTree.keySet());
            files.addAll(ourTree.keySet());
            files.addAll(theirTree.keySet());

            Map<String, String> merged = new HashMap<>();
            List<String> conflicts = new ArrayList<>();

            for (String file : files) {
                String baseValue = baseTree.get(file);
                String ourValue = ourTree.get(file);
                String theirValue = theirTree.get(file);

                if (Objects.equals(ourValue, theirValue)) {
                    if (ourValue != null) {
                        merged.put(file, ourValue);
                    }
                } else if (Objects.equals(ourValue, baseValue)) {
                    if (theirValue != null) {
                        merged.put(file, theirValue);
                    }
                } else if (Objects.equals(theirValue, baseValue)) {
                    if (ourValue != null) {
                        merged.put(file, ourValue);
                    }
                } else {
                    conflicts.add(file);
                }
            }

            if (!conflicts.isEmpty()) {
                state = RepositoryState.MERGING;
                throw new StateException(
                        "Merge conflicts: " +
                                String.join(", ", conflicts)
                );
            }

            workingTree.clear();
            workingTree.putAll(merged);
            index.clear();
            index.putAll(merged);

            state = RepositoryState.ACTIVE;

            return commit(
                    "Merge branch '" + sourceBranch +
                            "' into " + headBranch,
                    "merge-bot"
            );
        }

        boolean mergeEligible(ReviewPolicy policy, int approvals,
                               Set<String> passedChecks) {
            if (policy.requireCleanTree() && !isClean()) {
                return false;
            }

            if (approvals < policy.requiredApprovals()) {
                return false;
            }

            return passedChecks.containsAll(policy.requiredChecks());
        }

        String headBranch() {
            return headBranch;
        }

        RepositoryState state() {
            return state;
        }

        void printStatus() {
            System.out.println("\nSTATUS");
            EnumMap<FileState, List<String>> states = status();

            for (FileState state : FileState.values()) {
                System.out.printf(
                        "  %-10s %s%n",
                        state.name().toLowerCase(),
                        states.getOrDefault(state, List.of())
                );
            }
        }

        void printBranches() {
            System.out.println("\nBRANCHES");

            branches.values().forEach(branch ->
                    System.out.printf(
                            "  %-16s %s%n",
                            branch.name(),
                            branch.commitId().isBlank()
                                    ? "(empty)"
                                    : branch.commitId().substring(
                                            0, Math.min(
                                                    12,
                                                    branch.commitId().length()
                                            )
                                    )
                    )
            );
        }

        int objectCount() {
            return objects.size();
        }

        int commitCount() {
            return commits.size();
        }

        private static void validatePath(String file) {
            if (file == null
                    || file.isBlank()
                    || file.startsWith("/")
                    || file.contains("..")) {
                throw new ValidationException(
                        "Unsafe repository path: " + file
                );
            }
        }

        private static void validateBranch(String name) {
            if (name == null
                    || !SAFE_BRANCH.matcher(name).matches()
                    || name.startsWith("/")
                    || name.endsWith("/")
                    || name.contains("..")) {
                throw new ValidationException(
                        "Invalid branch name: " + name
                );
            }
        }

        private static String stableId(Object value) {
            return Integer.toHexString(
                    Objects.toString(value).hashCode()
            );
        }
    }

    static final class MergeEligibilityService {
        private MergeEligibilityService() {}

        static boolean evaluate(
                Repository repository,
                ReviewPolicy policy,
                int approvals,
                Set<String> checks
        ) {
            return repository.mergeEligible(
                    policy,
                    approvals,
                    checks
            );
        }
    }

    public static void main(String[] args) {
        Repository repository = new Repository();

        repository.writeFile(
                "README.md",
                "# Enterprise Repository\n"
        );
        repository.writeFile(
                "service.properties",
                "version=1\n"
        );
        repository.addAll();

        String initial = repository.commit(
                "Initialize enterprise repository",
                "developer@example.com"
        );

        repository.createBranch("feature/audit");
        repository.checkout("feature/audit");

        repository.writeFile(
                "audit.properties",
                "audit.enabled=true\n"
        );
        repository.add("audit.properties");

        String feature = repository.commit(
                "Add audit configuration",
                "security@example.com"
        );

        repository.checkout("main");

        repository.writeFile(
                "README.md",
                "# Enterprise Repository\nGovernance enabled\n"
        );
        repository.add("README.md");

        String mainUpdate = repository.commit(
                "Document governance workflow",
                "developer@example.com"
        );

        String merged = repository.merge("feature/audit");

        repository.printStatus();
        repository.printBranches();

        System.out.println("\nCOMMITS");
        System.out.println("initial: " + initial);
        System.out.println("feature: " + feature);
        System.out.println("main:    " + mainUpdate);
        System.out.println("merge:   " + merged);

        ReviewPolicy policy = new ReviewPolicy(
                2,
                Set.of("unit-tests", "security-scan"),
                true
        );

        Set<String> checks = Set.of(
                "unit-tests",
                "security-scan"
        );

        boolean eligible =
                MergeEligibilityService.evaluate(
                        repository,
                        policy,
                        2,
                        checks
                );

        System.out.println("\nMERGE ELIGIBILITY");
        System.out.println("required approvals: "
                + policy.requiredApprovals());
        System.out.println("required checks: "
                + policy.requiredChecks());
        System.out.println("eligible: " + eligible);

        try {
            repository.writeFile("../outside.txt", "blocked");
        } catch (ValidationException error) {
            System.out.println("\nUnsafe path rejected.");
        }

        repository.checkout(initial);
        System.out.println(
                "\nDetached historical state: " + repository.head()
        );

        repository.checkout("main");
        System.out.println(
                "Restored branch: " + repository.headBranch()
        );

        System.out.println("\nObjects: " + repository.objectCount());
        System.out.println("Commits: " + repository.commitCount());
        System.out.println("State: " + repository.state());
    }
}
