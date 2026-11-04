import java.util.*;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import java.util.stream.Collectors;

/*
 * Enterprise Package Management Governance System
 *
 * Java 17 implementation featuring:
 * - Immutable semantic versions
 * - Package manifest domain types
 * - Dependency classifications
 * - Version compatibility
 * - Enterprise installation policies
 * - Package registry
 * - Dependency resolution
 * - Lockfile verification
 * - Security advisories
 * - Release eligibility decisions
 */

public class PackageGovernance {

    static class PackageException extends RuntimeException {
        PackageException(String message) {
            super(message);
        }
    }

    record Version(int major, int minor, int patch)
            implements Comparable<Version> {

        private static final Pattern PATTERN =
                Pattern.compile(
                    "^(0|[1-9]\\d*)\\.(0|[1-9]\\d*)\\.(0|[1-9]\\d*)$"
                );

        Version {
            if (major < 0 || minor < 0 || patch < 0) {
                throw new PackageException("Negative version component.");
            }
        }

        static Version parse(String value) {
            Matcher matcher = PATTERN.matcher(value);

            if (!matcher.matches()) {
                throw new PackageException(
                    "Invalid semantic version: " + value
                );
            }

            return new Version(
                Integer.parseInt(matcher.group(1)),
                Integer.parseInt(matcher.group(2)),
                Integer.parseInt(matcher.group(3))
            );
        }

        @Override
        public int compareTo(Version other) {
            int result = Integer.compare(major, other.major);

            if (result != 0) return result;

            result = Integer.compare(minor, other.minor);

            if (result != 0) return result;

            return Integer.compare(patch, other.patch);
        }

        @Override
        public String toString() {
            return major + "." + minor + "." + patch;
        }
    }

    record VersionRange(String expression) {

        VersionRange {
            Objects.requireNonNull(expression);

            if (expression.isBlank()) {
                throw new PackageException("Empty version range.");
            }

            String base = expression;

            if (base.startsWith("^") || base.startsWith("~")) {
                base = base.substring(1);
            } else if (base.startsWith(">=") ||
                       base.startsWith("<=")) {
                base = base.substring(2);
            } else if (base.startsWith(">") ||
                       base.startsWith("<")) {
                base = base.substring(1);
            }

            if (!base.equals("*") && !base.equals("latest")) {
                Version.parse(base.trim());
            }
        }

        boolean accepts(Version candidate) {
            String value = expression.trim();

            if (value.equals("*") || value.equals("latest")) {
                return true;
            }

            String operator;
            String base;

            if (value.startsWith("^") || value.startsWith("~")) {
                operator = value.substring(0, 1);
                base = value.substring(1);
            } else if (value.startsWith(">=") ||
                       value.startsWith("<=")) {
                operator = value.substring(0, 2);
                base = value.substring(2).trim();
            } else if (value.startsWith(">") ||
                       value.startsWith("<")) {
                operator = value.substring(0, 1);
                base = value.substring(1).trim();
            } else {
                operator = "=";
                base = value;
            }

            Version expected = Version.parse(base);
            int comparison = candidate.compareTo(expected);

            return switch (operator) {
                case "^" -> {
                    if (comparison < 0) yield false;

                    if (expected.major() > 0) {
                        yield candidate.major() == expected.major();
                    }

                    if (expected.minor() > 0) {
                        yield candidate.major() == 0 &&
                              candidate.minor() == expected.minor();
                    }

                    yield candidate.major() == 0 &&
                          candidate.minor() == 0 &&
                          candidate.patch() == expected.patch();
                }
                case "~" -> candidate.compareTo(expected) >= 0 &&
                            candidate.major() == expected.major() &&
                            candidate.minor() == expected.minor();
                case ">=" -> comparison >= 0;
                case "<=" -> comparison <= 0;
                case ">" -> comparison > 0;
                case "<" -> comparison < 0;
                case "=" -> comparison == 0;
                default -> throw new PackageException(
                    "Unsupported version operator."
                );
            };
        }
    }

    enum DependencyType {
        PRODUCTION,
        DEVELOPMENT,
        OPTIONAL,
        PEER
    }

    enum ReleaseStatus {
        ACCEPTED,
        REJECTED
    }

    record Dependency(
            String packageName,
            VersionRange range,
            DependencyType type
    ) {
        Dependency {
            if (packageName == null || packageName.isBlank()) {
                throw new PackageException(
                    "Dependency name is required."
                );
            }

            Objects.requireNonNull(range);
            Objects.requireNonNull(type);
        }
    }

    record PackageArtifact(
            String name,
            Version version,
            Map<String, VersionRange> dependencies
    ) {
        PackageArtifact {
            Objects.requireNonNull(name);
            Objects.requireNonNull(version);

            if (name.isBlank()) {
                throw new PackageException("Empty package name.");
            }

            dependencies = Map.copyOf(dependencies);
        }
    }

    record ProjectManifest(
            String name,
            Version version,
            List<Dependency> dependencies,
            Map<String, String> scripts,
            String nodeEngine
    ) {
        ProjectManifest {
            if (name == null || name.isBlank()) {
                throw new PackageException(
                    "Project name is required."
                );
            }

            Objects.requireNonNull(version);

            dependencies = List.copyOf(dependencies);
            scripts = Map.copyOf(scripts);

            for (var entry : scripts.entrySet()) {
                if (
                    entry.getKey().isBlank() ||
                    entry.getValue().isBlank()
                ) {
                    throw new PackageException(
                        "Invalid npm script definition."
                    );
                }
            }
        }
    }

    static class PackageRegistry {

        private final Map<String, NavigableMap<Version, PackageArtifact>>
                artifacts = new HashMap<>();

        void publish(PackageArtifact artifact) {
            NavigableMap<Version, PackageArtifact> versions =
                    artifacts.computeIfAbsent(
                        artifact.name(),
                        key -> new TreeMap<>()
                    );

            if (versions.containsKey(artifact.version())) {
                throw new PackageException(
                    "Package version already published: " +
                    artifact.name()
                );
            }

            versions.put(artifact.version(), artifact);
        }

        PackageArtifact resolve(
                String name,
                List<VersionRange> constraints
        ) {
            NavigableMap<Version, PackageArtifact> versions =
                    artifacts.get(name);

            if (versions == null) {
                throw new PackageException(
                    "Package not found: " + name
                );
            }

            return versions.descendingMap()
                    .values()
                    .stream()
                    .filter(artifact ->
                        constraints.stream().allMatch(
                            range -> range.accepts(artifact.version())
                        )
                    )
                    .findFirst()
                    .orElseThrow(() ->
                        new PackageException(
                            "No compatible version for " + name
                        )
                    );
        }
    }

    static class DependencyResolver {

        private final PackageRegistry registry;

        DependencyResolver(PackageRegistry registry) {
            this.registry = registry;
        }

        Map<String, PackageArtifact> resolve(
                ProjectManifest manifest,
                boolean productionOnly
        ) {
            Map<String, List<VersionRange>> requirements =
                    new HashMap<>();

            Queue<String> pending = new ArrayDeque<>();

            for (Dependency dependency : manifest.dependencies()) {
                if (
                    productionOnly &&
                    dependency.type() == DependencyType.DEVELOPMENT
                ) {
                    continue;
                }

                requirements.computeIfAbsent(
                    dependency.packageName(),
                    key -> {
                        pending.add(key);
                        return new ArrayList<>();
                    }
                ).add(dependency.range());
            }

            Map<String, PackageArtifact> resolved =
                    new LinkedHashMap<>();

            while (!pending.isEmpty()) {
                String name = pending.remove();

                if (resolved.containsKey(name)) {
                    continue;
                }

                PackageArtifact artifact = registry.resolve(
                    name,
                    requirements.get(name)
                );

                resolved.put(name, artifact);

                for (var child : artifact.dependencies().entrySet()) {
                    String childName = child.getKey();

                    requirements.computeIfAbsent(
                        childName,
                        key -> {
                            pending.add(key);
                            return new ArrayList<>();
                        }
                    ).add(child.getValue());

                    PackageArtifact alreadyInstalled =
                            resolved.get(childName);

                    if (
                        alreadyInstalled != null &&
                        !child.getValue().accepts(
                            alreadyInstalled.version()
                        )
                    ) {
                        throw new PackageException(
                            "Transitive dependency conflict: " +
                            childName
                        );
                    }
                }
            }

            return Collections.unmodifiableMap(resolved);
        }
    }

    record SecurityAdvisory(
            String identifier,
            String packageName,
            VersionRange affectedRange,
            int severity
    ) {
        SecurityAdvisory {
            if (
                identifier == null ||
                packageName == null ||
                severity < 1 ||
                severity > 4
            ) {
                throw new PackageException(
                    "Invalid security advisory."
                );
            }
        }
    }

    static class SecurityService {

        private final List<SecurityAdvisory> advisories;

        SecurityService(List<SecurityAdvisory> advisories) {
            this.advisories = List.copyOf(advisories);
        }

        List<String> audit(
                Map<String, PackageArtifact> installed
        ) {
            return installed.values().stream()
                    .flatMap(artifact ->
                        advisories.stream()
                            .filter(advisory ->
                                advisory.packageName().equals(
                                    artifact.name()
                                ) &&
                                advisory.affectedRange().accepts(
                                    artifact.version()
                                )
                            )
                            .map(advisory ->
                                advisory.identifier() + " " +
                                advisory.packageName() + "@" +
                                artifact.version() +
                                " severity=" + advisory.severity()
                            )
                    )
                    .toList();
        }
    }

    record GovernancePolicy(
            int maximumAllowedSeverity,
            boolean requireProductionLockfile,
            boolean allowWildcardRanges,
            Set<String> permittedEngines
    ) {
        GovernancePolicy {
            if (
                maximumAllowedSeverity < 1 ||
                maximumAllowedSeverity > 4
            ) {
                throw new PackageException(
                    "Invalid severity threshold."
                );
            }

            permittedEngines = Set.copyOf(permittedEngines);
        }
    }

    record ReleaseDecision(
            ReleaseStatus status,
            List<String> violations
    ) {
        ReleaseDecision {
            violations = List.copyOf(violations);
        }
    }

    static class ReleaseEligibilityService {

        private final GovernancePolicy policy;
        private final SecurityService securityService;

        ReleaseEligibilityService(
                GovernancePolicy policy,
                SecurityService securityService
        ) {
            this.policy = policy;
            this.securityService = securityService;
        }

        ReleaseDecision evaluate(
                ProjectManifest manifest,
                Map<String, PackageArtifact> installed,
                boolean lockfileVerified
        ) {
            List<String> violations = new ArrayList<>();

            if (
                policy.requireProductionLockfile() &&
                !lockfileVerified
            ) {
                violations.add("Production lockfile verification failed.");
            }

            if (
                manifest.nodeEngine() == null ||
                !policy.permittedEngines().contains(
                    manifest.nodeEngine()
                )
            ) {
                violations.add("Node.js engine is not permitted.");
            }

            for (Dependency dependency : manifest.dependencies()) {
                if (
                    !policy.allowWildcardRanges() &&
                    dependency.range().expression().equals("*")
                ) {
                    violations.add(
                        "Unbounded dependency: " +
                        dependency.packageName()
                    );
                }
            }

            for (String finding : securityService.audit(installed)) {
                String severityText = finding.substring(
                    finding.lastIndexOf("severity=") + 9
                );

                int severity = Integer.parseInt(severityText);

                if (severity > policy.maximumAllowedSeverity()) {
                    violations.add(
                        "Security threshold exceeded: " + finding
                    );
                }
            }

            return new ReleaseDecision(
                violations.isEmpty()
                    ? ReleaseStatus.ACCEPTED
                    : ReleaseStatus.REJECTED,
                violations
            );
        }
    }

    public static void main(String[] args) {

        try {
            PackageRegistry registry = new PackageRegistry();

            registry.publish(new PackageArtifact(
                "express",
                Version.parse("4.21.0"),
                Map.of()
            ));

            registry.publish(new PackageArtifact(
                "express",
                Version.parse("4.21.1"),
                Map.of()
            ));

            registry.publish(new PackageArtifact(
                "pg",
                Version.parse("8.13.0"),
                Map.of()
            ));

            registry.publish(new PackageArtifact(
                "pg",
                Version.parse("8.14.0"),
                Map.of()
            ));

            registry.publish(new PackageArtifact(
                "api-client",
                Version.parse("2.2.0"),
                Map.of(
                    "express",
                    new VersionRange("^4.0.0")
                )
            ));

            registry.publish(new PackageArtifact(
                "jest",
                Version.parse("29.7.0"),
                Map.of()
            ));

            ProjectManifest manifest = new ProjectManifest(
                "enterprise-service",
                Version.parse("2.0.0"),
                List.of(
                    new Dependency(
                        "express",
                        new VersionRange("^4.0.0"),
                        DependencyType.PRODUCTION
                    ),
                    new Dependency(
                        "pg",
                        new VersionRange("^8.13.0"),
                        DependencyType.PRODUCTION
                    ),
                    new Dependency(
                        "api-client",
                        new VersionRange("^2.0.0"),
                        DependencyType.PRODUCTION
                    ),
                    new Dependency(
                        "jest",
                        new VersionRange("^29.0.0"),
                        DependencyType.DEVELOPMENT
                    )
                ),
                Map.of(
                    "start", "node server.js",
                    "test", "jest",
                    "build", "node build.js"
                ),
                "node-20"
            );

            System.out.println("PROJECT MANIFEST");
            System.out.println(manifest);

            DependencyResolver resolver =
                    new DependencyResolver(registry);

            System.out.println("\nPRODUCTION DEPENDENCIES");

            Map<String, PackageArtifact> production =
                    resolver.resolve(manifest, true);

            production.values().forEach(System.out::println);

            System.out.println("\nCOMPLETE DEPENDENCY TREE");

            Map<String, PackageArtifact> complete =
                    resolver.resolve(manifest, false);

            complete.values().forEach(System.out::println);

            List<SecurityAdvisory> advisories = List.of(
                new SecurityAdvisory(
                    "SEC-2026-001",
                    "express",
                    new VersionRange("<4.21.1"),
                    4
                ),
                new SecurityAdvisory(
                    "SEC-2026-002",
                    "pg",
                    new VersionRange("<8.14.0"),
                    2
                )
            );

            SecurityService security =
                    new SecurityService(advisories);

            System.out.println("\nSECURITY AUDIT");

            List<String> findings = security.audit(complete);

            if (findings.isEmpty()) {
                System.out.println("No matching advisories.");
            } else {
                findings.forEach(System.out::println);
            }

            GovernancePolicy policy = new GovernancePolicy(
                2,
                true,
                false,
                Set.of("node-20")
            );

            ReleaseEligibilityService releaseService =
                    new ReleaseEligibilityService(policy, security);

            System.out.println("\nRELEASE ELIGIBILITY");

            ReleaseDecision decision = releaseService.evaluate(
                manifest,
                production,
                true
            );

            System.out.println("Status: " + decision.status());

            decision.violations().forEach(
                violation -> System.out.println("BLOCKED: " + violation)
            );

            System.out.println("\nSEMVER TESTS");

            Version current = Version.parse("2.4.1");

            System.out.println(
                "^2.0.0: " +
                new VersionRange("^2.0.0").accepts(current)
            );

            System.out.println(
                "~2.4.0: " +
                new VersionRange("~2.4.0").accepts(current)
            );

            System.out.println(
                "^3.0.0: " +
                new VersionRange("^3.0.0").accepts(current)
            );

            System.out.println("\nEnterprise package evaluation completed.");

        } catch (PackageException exception) {
            System.err.println(
                "PACKAGE GOVERNANCE FAILURE: " +
                exception.getMessage()
            );

            System.exit(1);
        }
    }
}
