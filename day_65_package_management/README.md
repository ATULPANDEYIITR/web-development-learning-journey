# Package Management: npm, package.json, Dependencies and Semantic Versioning

## 1. Project Overview

This project examines package management as an application development and software supply-chain engineering discipline.

It uses five independent implementations to model package manifests, dependency declarations, package registries, version compatibility, installation policies, lockfiles, npm scripts, security auditing, and release eligibility.

The implementations use different engineering approaches:

| Implementation | Engineering perspective |
|---|---|
| Python | Package workflow simulation and dependency resolution |
| JavaScript | Node.js package manifest inspection and event-driven script management |
| C++17 | Efficient package registry and dependency governance |
| Java 17 | Enterprise package governance and release eligibility |
| PostgreSQL | Relational package registry, installation records, and policy evaluation |

The examples use an enterprise API and dashboard development environment.

## 2. Package Management Fundamentals

Package management is the process of identifying, acquiring, configuring, installing, updating, and maintaining software components required by an application.

A package generally contains:

- Application code or reusable functionality.
- A package name and version.
- Dependency declarations.
- Metadata.
- Distribution information.
- Integrity information.
- Compatibility requirements.

A package manager automates the relationship between an application and its required packages.

### 2.1 npm

`npm` is the default package manager distributed with Node.js.

Its principal responsibilities include:

- Installing packages from registries.
- Removing packages.
- Updating dependencies.
- Managing package versions.
- Executing project scripts.
- Maintaining installation metadata.
- Resolving dependency relationships.
- Generating and maintaining `package-lock.json`.
- Running security audits.

Important npm commands include:

| Command | Purpose |
|---|---|
| `npm init` | Creates a package manifest |
| `npm install` | Installs project dependencies |
| `npm install express` | Adds a production dependency |
| `npm install --save-dev jest` | Adds a development dependency |
| `npm uninstall express` | Removes a dependency |
| `npm update` | Updates dependencies within permitted ranges |
| `npm ci` | Performs a clean lockfile-based installation |
| `npm ls` | Displays the installed dependency tree |
| `npm audit` | Checks known dependency vulnerabilities |
| `npm run build` | Executes the build script |
| `npm run test` | Executes the test script |

`npm install` and `npm ci` have different operational purposes.

`npm install` can modify the lockfile when dependency declarations change. `npm ci` requires a compatible lockfile, removes the existing `node_modules` directory, and installs the locked dependency tree.

For automated production builds, lockfile-based installation provides greater reproducibility.

## 3. package.json

`package.json` is the central metadata and configuration file of an npm project.

It describes the application, its dependencies, supported runtime requirements, and executable scripts.

Important properties include:

| Property | Purpose |
|---|---|
| `name` | Identifies the package |
| `version` | Identifies the package release |
| `description` | Describes the package |
| `main` | Specifies a traditional package entry point |
| `type` | Determines JavaScript module interpretation |
| `scripts` | Defines executable project commands |
| `dependencies` | Defines runtime dependencies |
| `devDependencies` | Defines development dependencies |
| `peerDependencies` | Defines compatibility expectations with host packages |
| `optionalDependencies` | Defines dependencies whose installation may be optional |
| `engines` | Declares supported runtime versions |
| `overrides` | Controls selected transitive dependency versions |
| `files` | Controls which files are included in a published package |

A valid project manifest should use a valid package name, a valid package version, appropriate dependency ranges, and correctly structured objects.

### 3.1 Production dependencies

The `dependencies` property contains packages required by the application during normal operation.

Examples include:

- Express for HTTP application development.
- PostgreSQL clients for database access.
- Authentication libraries.
- Runtime validation libraries.
- Logging components.

Production dependencies are required when deploying the application.

### 3.2 Development dependencies

The `devDependencies` property contains packages used during software development, testing, building, and quality assurance.

Examples include:

- TypeScript.
- Jest.
- ESLint.
- Build tools.
- Testing frameworks.

These packages are not automatically required by the application at runtime.

A production deployment should exclude development dependencies when the deployment architecture does not require them.

### 3.3 Optional dependencies

`optionalDependencies` identifies packages whose installation failure does not necessarily prevent the application from installing.

Applications must handle their absence when they rely on optional functionality.

### 3.4 Peer dependencies

`peerDependencies` expresses compatibility requirements between a package and another package supplied by its consuming application.

This mechanism is common in reusable libraries and plugins.

A peer dependency is not simply another ordinary runtime dependency. It communicates an expected relationship with the host application's package environment.

## 4. npm Scripts

The `scripts` property defines named commands associated with project workflows.

Common scripts include:

| Script | Typical responsibility |
|---|---|
| `start` | Starts the application |
| `dev` | Starts a development environment |
| `build` | Compiles or bundles application code |
| `test` | Executes automated tests |
| `lint` | Checks code quality |
| `format` | Applies formatting rules |
| `prepare` | Performs package preparation tasks |
| `pretest` | Runs before the test script |
| `posttest` | Runs after the test script |

npm supports lifecycle scripts and automatic pre/post execution for applicable user-defined scripts.

For example, executing `npm run test` can invoke `pretest`, `test`, and `posttest` in the appropriate lifecycle sequence.

Scripts are executable commands, not passive metadata.

Their security implications include:

- Arbitrary shell command execution.
- Access to environment variables.
- File-system modifications.
- Network communication.
- Execution of installed package scripts.

Production automation should therefore use reviewed scripts, controlled environments, restricted permissions, and execution timeouts.

The JavaScript implementation models script execution through an event-driven lifecycle. It separates script registration, execution, success, and failure events.

It uses a controlled demonstration executor instead of automatically executing arbitrary manifest commands.

## 5. Semantic Versioning

Semantic Versioning, commonly abbreviated as SemVer, communicates compatibility expectations through structured version numbers.

The standard version structure is:

`MAJOR.MINOR.PATCH`

For example:

`3.7.2`

| Component | Meaning | Typical release condition |
|---|---|---|
| MAJOR | Incompatible API changes | Breaking changes |
| MINOR | Backward-compatible functionality | New features |
| PATCH | Backward-compatible corrections | Bug fixes |

### 5.1 Major versions

A major release communicates potentially incompatible changes.

For example:

`3.0.0` to `4.0.0`

Applications may need source-code modifications before adopting the new version.

### 5.2 Minor versions

A minor release introduces backward-compatible functionality.

For example:

`3.2.0` to `3.3.0`

Applications using the previous minor release should generally continue working when the package follows SemVer correctly.

### 5.3 Patch versions

A patch release introduces backward-compatible fixes.

For example:

`3.2.1` to `3.2.2`

Patch releases are generally the smallest compatibility change.

### 5.4 Prerelease versions

Prerelease identifiers indicate versions that precede a normal release.

Examples:

- `2.0.0-alpha.1`
- `2.0.0-beta.2`
- `2.0.0-rc.1`

Prerelease versions require careful compatibility handling.

Build metadata, introduced through a plus sign, does not affect semantic version precedence.

For example, `2.1.0+build.15` contains build metadata.

The source implementations use a deliberately restricted SemVer subset for their dependency evaluation demonstrations. The Python, C++, Java, and PostgreSQL examples primarily support three-component stable versions. The JavaScript implementation also parses prerelease and build metadata but uses a simplified comparison model.

A complete npm-compatible implementation must account for prerelease precedence, complex range expressions, comparator sets, hyphen ranges, and additional SemVer rules.

## 6. npm Version Range Operators

A dependency does not necessarily specify one exact package version.

It can specify a range of acceptable versions.

| Operator | Meaning | Example |
|---|---|---|
| `^` | Compatible updates within the permitted major or zero-major boundary | `^2.4.0` |
| `~` | Compatible patch updates within the same minor version | `~2.4.0` |
| `>=` | Minimum version | `>=2.4.0` |
| `<=` | Maximum version | `<=2.4.9` |
| `>` | Greater than a version | `>2.4.0` |
| `<` | Less than a version | `<3.0.0` |
| Exact | One specified version | `2.4.1` |
| `*` | Any version | `*` |

The distinction between caret and tilde ranges is important.

For example:

- `^2.4.0` allows compatible updates below `3.0.0`.
- `~2.4.0` allows compatible updates within the `2.4.x` series.

Zero-major versions have more restrictive caret behavior.

For example, `^0.4.0` does not permit updates to `0.5.0` under standard npm SemVer range interpretation.

Unbounded ranges can introduce unexpected dependency changes. Production projects should use deliberate version constraints and maintain a verified lockfile.

## 7. Dependency Resolution

Dependency resolution determines which package versions can be installed together.

Consider this application:

- The application requires Express `^4.0.0`.
- An API client also requires Express `^4.0.0`.
- The registry contains Express `4.21.0`, `4.21.1`, and `5.0.0`.

The resolver selects the highest compatible available version, `4.21.1`.

The version `5.0.0` is excluded because it violates the declared compatibility range.

### 7.1 Direct dependencies

A direct dependency is explicitly declared by the application.

For example, an application can directly declare Express and PostgreSQL client packages.

### 7.2 Transitive dependencies

A transitive dependency is introduced through another package.

For example:

Application
→ API Client
→ Express

The application may not directly declare every package in its installed dependency tree.

Transitive dependencies must still be considered during security auditing and compatibility evaluation.

### 7.3 Dependency conflicts

Conflicts occur when multiple requirements cannot be satisfied by one selected version under the resolver's supported model.

For example:

- Package A requires library X `^2.0.0`.
- Package B requires library X `^3.0.0`.

A simple single-version resolver cannot satisfy both requirements simultaneously.

npm can sometimes install multiple versions of a package at different positions in the dependency tree. This project uses a simplified single-version-per-package resolution model to demonstrate conflict detection.

### 7.4 Dependency graphs

Dependencies naturally form a directed graph.

A graph representation supports:

- Transitive dependency discovery.
- Dependency conflict identification.
- Installation ordering.
- Circular dependency detection.
- Impact analysis.
- Security exposure analysis.

A production dependency resolver must also consider optional dependencies, peer dependencies, platform restrictions, package aliases, workspaces, and package-manager-specific installation behavior.

## 8. package-lock.json

`package-lock.json` records the resolved dependency tree of an npm project.

It complements `package.json`.

The two files have different responsibilities:

| File | Responsibility |
|---|---|
| `package.json` | Declares intended dependencies and permitted ranges |
| `package-lock.json` | Records the concrete dependency resolution |

A lockfile can contain:

- Exact package versions.
- Dependency relationships.
- Resolved package locations.
- Integrity hashes.
- Dependency classification.
- Installation metadata.

Lockfiles are important for:

- Reproducible development environments.
- Consistent CI/CD installations.
- Controlled production releases.
- Dependency change reviews.
- Security investigations.

The Python implementation verifies direct dependency compatibility against its generated lock representation.

The JavaScript implementation inspects a simplified npm lockfile version 3 structure.

The SQL implementation stores lockfile metadata and exact locked package versions in relational tables.

A hash stored in a database is not proof of integrity by itself. A production implementation must independently obtain trusted registry integrity metadata and verify downloaded package contents against it.

## 9. Package Registry and Installation Workflow

A package registry stores published package artifacts and their metadata.

The implementations model a registry containing multiple versions of individual packages.

The logical installation workflow is:

Project Manifest
→ Dependency Declarations
→ Version Constraints
→ Package Registry
→ Version Resolution
→ Transitive Dependency Resolution
→ Lockfile
→ Installation
→ Verification

A production installation should also consider:

- Registry authentication.
- Package provenance.
- Integrity verification.
- Network failures.
- Registry availability.
- Dependency lifecycle scripts.
- Platform-specific packages.
- Disk-space limitations.
- Reproducible build requirements.

The registry in the Python, C++, and Java implementations is an in-memory model rather than a network-connected npm registry.

## 10. Security and Supply-Chain Governance

Package management is a significant software supply-chain security concern.

An application inherits potential security weaknesses from its direct and transitive dependencies.

### 10.1 Vulnerability auditing

A security advisory identifies an affected package and version range.

An audit compares installed versions with known advisory ranges.

For example:

| Package | Installed version | Affected range | Result |
|---|---|---|---|
| Express | 4.21.1 | Below 4.21.1 | Not affected by the modeled advisory |
| PostgreSQL client | 8.13.0 | Below 8.14.0 | Affected by the modeled advisory |
| Lodash | 4.17.20 | Below 4.17.21 | Affected by the modeled advisory |

The advisories in these implementations are demonstration records. They are not assertions about current real-world vulnerabilities.

### 10.2 Security controls

A production package governance process should enforce:

- Trusted package registries.
- Registry authentication.
- Package integrity verification.
- Dependency lockfiles.
- Vulnerability scanning.
- Dependency update reviews.
- Restricted installation permissions.
- Controlled lifecycle script execution.
- Package provenance verification.
- Secret protection.
- Dependency inventory retention.

### 10.3 Integrity verification

Package integrity verification checks whether the downloaded artifact matches its expected cryptographic digest.

SHA-256 is used in the database model to represent artifact integrity metadata.

The integrity value must originate from a trusted source. A digest calculated from an untrusted downloaded artifact and stored without independent comparison does not establish authenticity.

### 10.4 Dependency governance

A package governance policy can define:

- Permitted runtime versions.
- Maximum vulnerability severity.
- Required lockfile verification.
- Dependency range restrictions.
- Integrity verification requirements.
- Release approval conditions.

The Java implementation combines these controls into a release eligibility service.

## 11. Python Implementation

The Python program models package management through object-oriented domain classes.

### Main components

| Component | Responsibility |
|---|---|
| `Version` | Parses and represents semantic versions |
| `VersionRange` | Evaluates supported version constraints |
| `Project` | Represents package.json metadata |
| `Package` | Represents a registry package |
| `PackageRegistry` | Stores and resolves available package versions |
| `PackageManager` | Resolves dependencies and builds a lock representation |
| `SecurityAuditor` | Evaluates installed packages against advisories |
| `ScriptRunner` | Inspects npm script commands |

### Workflow

The program creates an enterprise dashboard manifest, validates its metadata, populates an in-memory package registry, and resolves production and development dependencies.

It then verifies the lock representation and audits installed packages against a demonstration vulnerability database.

Script inspection is separated from execution to avoid automatically launching arbitrary commands.

### Important design decisions

- Dataclasses represent package-domain objects.
- Dictionaries provide efficient package lookup.
- Sets and queues support dependency processing.
- Exceptions represent invalid manifests and resolution failures.
- Assertions validate important version-range conditions.

For V resolved packages and E dependency edges, graph traversal is approximately O(V + E), excluding registry candidate selection.

The demonstration registry uses sorted version lists and selects the highest compatible version.

## 12. JavaScript Implementation

The JavaScript implementation uses Node.js-specific features to model package management as an event-driven process.

### Main components

| Component | Responsibility |
|---|---|
| `PackageManifest` | Validates package metadata |
| `LockfileInspector` | Checks lockfile compatibility |
| `InstallPolicy` | Evaluates installation restrictions |
| `ScriptLifecycle` | Manages asynchronous npm script events |
| `DependencyAuditor` | Evaluates vulnerability advisories |
| `createIntegrityFingerprint` | Creates a SHA-256 metadata fingerprint |

### Event-driven script lifecycle

The script lifecycle uses Node.js `EventEmitter`.

Its events include:

- `script:start`
- `script:success`
- `script:failure`

This separates command registration, execution, and result reporting.

Promises provide asynchronous execution behavior.

The demonstration executor validates a command and returns a controlled result. It does not execute arbitrary shell commands from package metadata.

### Lockfile inspection

The JavaScript implementation examines a simplified npm lockfile structure.

It checks whether direct dependencies have compatible versions in the lockfile root metadata.

This is a focused consistency check rather than a complete implementation of npm's installation algorithm.

### Integrity fingerprint

The SHA-256 fingerprint records a deterministic representation of the supplied manifest and lockfile objects.

It is useful for demonstrating change detection. It is not a replacement for package artifact integrity verification or digital signatures.

## 13. C++17 Implementation

The C++ program models package resolution and deployment security using strongly typed domain structures.

### Main components

| Component | Responsibility |
|---|---|
| `Version` | Represents a comparable semantic version |
| `VersionConstraint` | Evaluates supported version expressions |
| `Package` | Represents a published artifact |
| `PackageProject` | Holds project dependency declarations |
| `Registry` | Stores available package versions |
| `DependencyResolver` | Resolves direct and transitive dependencies |
| `SecurityPolicy` | Evaluates vulnerability severity |

### Dependency resolution

The registry uses a map from package names to sorted version collections.

The resolver maintains:

- A map of package requirements.
- A processed package set.
- A resulting installation collection.

The registry chooses the highest version satisfying all currently known constraints.

When an already resolved package receives an incompatible transitive requirement, the resolver reports a conflict.

### Production and development separation

The resolver supports two modes:

- Production installation excludes development dependencies.
- Complete installation includes development dependencies.

This distinction demonstrates why build-time packages should not automatically become runtime deployment requirements.

### Deployment security

The security policy evaluates package versions against advisory ranges.

The deployment decision is based on a maximum allowed severity.

This approach illustrates policy-based installation governance rather than simply displaying vulnerability findings.

The implementation uses the C++ Standard Library and requires no external package-management libraries.

## 14. Java 17 Implementation

The Java program models enterprise package governance using immutable records, domain types, service classes, and explicit policy decisions.

### Main components

| Component | Responsibility |
|---|---|
| `Version` | Immutable semantic version |
| `VersionRange` | Version compatibility evaluation |
| `Dependency` | Typed dependency declaration |
| `PackageArtifact` | Published package representation |
| `ProjectManifest` | Immutable project metadata |
| `PackageRegistry` | Package version repository |
| `DependencyResolver` | Dependency resolution |
| `SecurityService` | Vulnerability evaluation |
| `GovernancePolicy` | Enterprise policy definition |
| `ReleaseEligibilityService` | Final release decision |

### Enterprise policy evaluation

The release eligibility service evaluates:

1. Lockfile verification.
2. Runtime engine compatibility.
3. Wildcard dependency restrictions.
4. Vulnerability severity thresholds.

It produces an immutable release decision containing an acceptance status and the corresponding violations.

This separates the policy definition from the operational service that evaluates it.

### State and validation

Java records provide concise immutable domain representations.

Collections are defensively copied to reduce unintended modification.

Custom exceptions communicate package governance failures.

Streams support advisory filtering and audit reporting.

The architecture is suitable as a foundation for a larger service that integrates a real package registry, persistent audit records, CI/CD systems, and enterprise identity controls.

## 15. PostgreSQL Implementation

The PostgreSQL implementation models package management as a relational data system.

It uses a dedicated `package_management` schema.

### 15.1 Relational entities

| Table | Purpose |
|---|---|
| `projects` | Application projects |
| `packages` | Package registry metadata |
| `package_versions` | Published package versions |
| `project_dependencies` | Direct project dependency declarations |
| `package_dependencies` | Transitive package relationships |
| `lockfiles` | Lockfile metadata |
| `locked_packages` | Exact package versions in a lockfile |
| `npm_scripts` | Project script definitions |
| `security_advisories` | Package vulnerability records |
| `installations` | Installation execution records |
| `release_policies` | Enterprise installation and release policies |
| `release_evaluations` | Recorded policy decisions |

### 15.2 Relationship model

Projects
→ Project Dependencies
→ Packages
→ Package Versions

Packages
→ Package Dependencies
→ Transitive Packages

Projects
→ Lockfiles
→ Locked Packages
→ Exact Package Versions

Packages
→ Security Advisories

Projects
→ Release Policies
→ Release Evaluations

Projects
→ npm Scripts

Projects
→ Installation Records

### 15.3 Integrity enforcement

The schema uses:

- Primary keys.
- Foreign keys.
- Unique constraints.
- Check constraints.
- Enumerated types.
- Indexes.

The `package_versions` table prevents duplicate package versions.

The dependency tables enforce valid relationships between projects and packages.

The lockfile tables maintain references to exact published versions.

A trigger prevents publishing additional versions of withdrawn packages.

### 15.4 Database functions

`semver_compare` compares stable three-component versions.

`semver_satisfies` evaluates the supported version-range operators.

`evaluate_project_release` evaluates the project against its configured release policy and stores a decision with structured JSON findings.

The release evaluation considers lockfile verification, wildcard dependencies, known advisories, vulnerability severity, and package integrity metadata.

### 15.5 Reporting and evaluation

The SQL script includes queries for:

- Project dependency inventory.
- Production and development dependency aggregation.
- Lockfile contents.
- Direct dependency compatibility.
- Vulnerability auditing.
- Release eligibility.
- npm script inventory.
- Installation history.
- Integrity mismatches.
- Database statistics.

The script also demonstrates transactional installation recording and release evaluation.

The vulnerability and integrity records are illustrative. A production database should integrate verified registry metadata and an authoritative advisory feed.

## 16. Differences Between Dependency Categories

The four dependency categories represent different package relationships.

| Category | Primary meaning | Typical usage |
|---|---|---|
| `dependencies` | Packages needed by the application | Runtime libraries |
| `devDependencies` | Packages needed during development | Testing and building |
| `optionalDependencies` | Packages that may be absent without necessarily preventing installation | Platform-specific enhancements |
| `peerDependencies` | Packages expected from the consuming environment | Plugins and reusable libraries |

These classifications should not be treated as interchangeable.

For example, a reusable UI plugin may expect the host application to provide a compatible framework through `peerDependencies`.

A standalone application may declare its runtime framework directly in `dependencies`.

A testing framework generally belongs in `devDependencies`.

## 17. Performance and Reliability Considerations

Package management performance depends on dependency graph size, registry access, package download volume, and installation behavior.

Important considerations include:

| Area | Engineering consideration |
|---|---|
| Registry lookup | Cache package metadata where appropriate |
| Dependency resolution | Avoid repeated resolution of processed nodes |
| Lockfiles | Reuse verified dependency resolutions |
| Installation | Use reproducible lockfile-based processes |
| Network | Handle timeouts and registry failures |
| Security | Audit direct and transitive dependencies |
| Storage | Avoid unnecessary duplicate package downloads |
| Automation | Apply execution timeouts and controlled permissions |
| Monitoring | Retain installation and audit records |

The in-memory resolvers in these examples use simplified single-version resolution. Real npm dependency trees can contain multiple installed versions of the same package.

The SQL implementation uses indexes on common lookup and relationship columns to improve joins and filtering.

## 18. Technical Limitations

These implementations are educational package-management models, not complete replacements for npm.

| Area | Implementation limitation |
|---|---|
| SemVer | Only a subset of npm range semantics is implemented |
| Registry | Package registries are represented in memory or relational tables |
| Installation | Actual package downloads are not performed |
| Lockfile | Simplified lockfile representations are used |
| Security audit | Demonstration advisory records are used |
| Integrity | Hash comparison is modeled without a complete trusted artifact-verification pipeline |
| Scripts | Arbitrary npm script execution is intentionally restricted |
| Dependency resolution | Simplified single-version resolution does not reproduce every npm tree-placement rule |
| Workspaces | npm workspace resolution is not implemented |
| Peer dependencies | Full npm peer dependency conflict resolution is not implemented |

The PostgreSQL version comparison function supports stable three-component versions. It does not implement prerelease precedence or the full npm range grammar.

A production-grade package governance system would require a fully compatible SemVer implementation, complete npm lockfile parsing, authenticated registry access, artifact verification, and a comprehensive dependency resolution strategy.

## 19. Practical Engineering Applications

The implemented mechanisms correspond to common software engineering workflows.

| Scenario | Relevant mechanism |
|---|---|
| Starting a Node.js project | `npm init` and `package.json` |
| Adding a runtime library | `dependencies` |
| Adding testing tools | `devDependencies` |
| Controlling compatible updates | Semantic version ranges |
| Reproducing CI installations | `package-lock.json` and `npm ci` |
| Executing project automation | npm scripts |
| Detecting incompatible requirements | Dependency resolution |
| Evaluating transitive risks | Security auditing |
| Restricting production dependencies | Installation policies |
| Recording deployment decisions | Release eligibility evaluation |

Together, the five implementations demonstrate how package management connects application metadata, dependency resolution, software installation, reproducibility, security, and enterprise release governance.
