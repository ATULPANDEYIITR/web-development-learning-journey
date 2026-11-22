import React, { useMemo, useState, useCallback } from "react";
import { createRoot } from "react-dom/client";
import "./styles.css";

/*
 * Production-style repository administration dashboard.
 *
 * Features:
 * - Interactive metrics
 * - Repository and Pull Request management
 * - Search and filtering
 * - Review and approval visibility
 * - CI status monitoring
 * - Branch protection monitoring
 * - Merge eligibility
 * - Audit events
 * - Event-driven state management
 *
 * Runtime: React 18+ with a modern JavaScript bundler.
 */

const initialRepositories = [
  {
    id: 1,
    name: "admin-platform",
    owner: "platform-team",
    visibility: "Private",
    defaultBranch: "main",
    updated: "2026-11-22",
  },
  {
    id: 2,
    name: "payment-service",
    owner: "backend-team",
    visibility: "Private",
    defaultBranch: "main",
    updated: "2026-11-21",
  },
  {
    id: 3,
    name: "analytics-engine",
    owner: "data-team",
    visibility: "Internal",
    defaultBranch: "main",
    updated: "2026-11-20",
  },
  {
    id: 4,
    name: "security-monitor",
    owner: "security-team",
    visibility: "Private",
    defaultBranch: "main",
    updated: "2026-11-19",
  },
];

const initialPullRequests = [
  {
    id: 1042,
    title: "Implement analytics dashboard",
    repository: "admin-platform",
    author: "atul",
    source: "feature/analytics",
    target: "main",
    status: "Open",
    approvals: 2,
    requiredApprovals: 2,
    checks: "Passed",
    unresolved: 0,
    draft: false,
    updated: "12 minutes ago",
  },
  {
    id: 1041,
    title: "Improve authentication middleware",
    repository: "payment-service",
    author: "alex",
    source: "feature/auth",
    target: "main",
    status: "Open",
    approvals: 1,
    requiredApprovals: 2,
    checks: "Running",
    unresolved: 2,
    draft: false,
    updated: "38 minutes ago",
  },
  {
    id: 1040,
    title: "Update security dependencies",
    repository: "security-monitor",
    author: "sam",
    source: "security/dependencies",
    target: "main",
    status: "Open",
    approvals: 2,
    requiredApprovals: 2,
    checks: "Failed",
    unresolved: 0,
    draft: false,
    updated: "1 hour ago",
  },
  {
    id: 1039,
    title: "Refactor analytics queries",
    repository: "analytics-engine",
    author: "maria",
    source: "feature/query-optimization",
    target: "main",
    status: "Draft",
    approvals: 0,
    requiredApprovals: 2,
    checks: "Pending",
    unresolved: 1,
    draft: true,
    updated: "3 hours ago",
  },
  {
    id: 1038,
    title: "Fix database connection handling",
    repository: "payment-service",
    author: "alex",
    source: "fix/database-pool",
    target: "main",
    status: "Merged",
    approvals: 2,
    requiredApprovals: 2,
    checks: "Passed",
    unresolved: 0,
    draft: false,
    updated: "Yesterday",
  },
];

const initialAudit = [
  {
    id: 1,
    actor: "atul",
    action: "Pull Request approved",
    target: "PR #1042",
    time: "12 minutes ago",
    type: "success",
  },
  {
    id: 2,
    actor: "ci-system",
    action: "Build completed",
    target: "PR #1040",
    time: "25 minutes ago",
    type: "danger",
  },
  {
    id: 3,
    actor: "administrator",
    action: "Branch protection updated",
    target: "admin-platform/main",
    time: "42 minutes ago",
    type: "info",
  },
  {
    id: 4,
    actor: "alex",
    action: "Pull Request submitted",
    target: "PR #1041",
    time: "1 hour ago",
    type: "info",
  },
];

const navigation = [
  { id: "overview", label: "Overview", icon: "◫" },
  { id: "repositories", label: "Repositories", icon: "▤" },
  { id: "pull-requests", label: "Pull Requests", icon: "⑂" },
  { id: "reviews", label: "Code Reviews", icon: "◎" },
  { id: "branches", label: "Branch Protection", icon: "⌑" },
  { id: "checks", label: "Status Checks", icon: "✓" },
  { id: "audit", label: "Audit Logs", icon: "≡" },
];

const statusClass = (value) => {
  const normalized = String(value).toLowerCase();

  if (["passed", "merged", "success", "approved"].includes(normalized)) {
    return "status-success";
  }

  if (["failed", "rejected", "changes requested"].includes(normalized)) {
    return "status-danger";
  }

  if (["running", "pending", "open"].includes(normalized)) {
    return "status-warning";
  }

  return "status-neutral";
};

function isMergeEligible(pr) {
  return (
    pr.status === "Open" &&
    !pr.draft &&
    pr.approvals >= pr.requiredApprovals &&
    pr.checks === "Passed" &&
    pr.unresolved === 0
  );
}

function Icon({ children }) {
  return <span className="icon">{children}</span>;
}

function Badge({ children, type }) {
  return (
    <span className={`badge ${type || statusClass(children)}`}>
      {children}
    </span>
  );
}

function MetricCard({ title, value, detail, icon, color }) {
  return (
    <article className="metric-card">
      <div className="metric-top">
        <span className="metric-label">{title}</span>
        <span className={`metric-icon ${color}`}>{icon}</span>
      </div>
      <div className="metric-value">{value}</div>
      <div className="metric-detail">{detail}</div>
    </article>
  );
}

function Sidebar({ active, setActive }) {
  return (
    <aside className="sidebar">
      <div className="brand">
        <div className="brand-symbol">N</div>
        <div>
          <strong>NEXUS</strong>
          <span>ADMIN CONSOLE</span>
        </div>
      </div>

      <div className="workspace">
        <div className="workspace-avatar">E</div>
        <div>
          <strong>Engineering</strong>
          <span>Enterprise workspace</span>
        </div>
        <span className="workspace-arrow">⌄</span>
      </div>

      <div className="nav-label">WORKSPACE</div>

      <nav>
        {navigation.map((item) => (
          <button
            key={item.id}
            className={`nav-item ${active === item.id ? "active" : ""}`}
            onClick={() => setActive(item.id)}
            type="button"
          >
            <Icon>{item.icon}</Icon>
            {item.label}
            {item.id === "pull-requests" && (
              <span className="nav-count">3</span>
            )}
          </button>
        ))}
      </nav>

      <div className="sidebar-bottom">
        <div className="system-status">
          <span className="online-dot" />
          All systems operational
        </div>
        <div className="profile">
          <div className="profile-avatar">AP</div>
          <div>
            <strong>Admin User</strong>
            <span>Administrator</span>
          </div>
          <span className="workspace-arrow">···</span>
        </div>
      </div>
    </aside>
  );
}

function Header({ active, search, setSearch }) {
  const current = navigation.find((item) => item.id === active);

  return (
    <header className="header">
      <div className="breadcrumb">
        <span>Workspace</span>
        <span>/</span>
        <strong>{current?.label || "Overview"}</strong>
      </div>

      <div className="header-actions">
        <label className="search-box">
          <span>⌕</span>
          <input
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Search repositories, PRs..."
            aria-label="Search dashboard"
          />
          <kbd>⌘ K</kbd>
        </label>

        <button
          className="icon-button"
          type="button"
          title="Notifications"
          aria-label="Notifications"
        >
          ♧
          <span className="notification-dot" />
        </button>

        <button className="icon-button" type="button" aria-label="Settings">
          ⚙
        </button>
      </div>
    </header>
  );
}

function Overview({
  repositories,
  pullRequests,
  audit,
  onMerge,
  onSelectPR,
}) {
  const metrics = useMemo(() => {
    const open = pullRequests.filter((pr) => pr.status === "Open").length;
    const merged = pullRequests.filter((pr) => pr.status === "Merged").length;
    const eligible = pullRequests.filter(isMergeEligible).length;

    return {
      repositories: repositories.length,
      open,
      merged,
      eligible,
    };
  }, [repositories, pullRequests]);

  return (
    <>
      <div className="page-heading">
        <div>
          <div className="eyebrow">ENGINEERING OPERATIONS</div>
          <h1>Dashboard Overview</h1>
          <p>Monitor repository activity, reviews and governance.</p>
        </div>
        <button className="primary-button" onClick={() => onSelectPR(null)}>
          + New Pull Request
        </button>
      </div>

      <section className="metrics-grid">
        <MetricCard
          title="Total Repositories"
          value={metrics.repositories}
          detail="Across engineering workspace"
          icon="▤"
          color="purple"
        />
        <MetricCard
          title="Open Pull Requests"
          value={metrics.open}
          detail="Awaiting workflow completion"
          icon="⑂"
          color="blue"
        />
        <MetricCard
          title="Merged Pull Requests"
          value={metrics.merged}
          detail="Recorded successfully"
          icon="✓"
          color="green"
        />
        <MetricCard
          title="Merge Eligible"
          value={metrics.eligible}
          detail="All configured conditions met"
          icon="◈"
          color="orange"
        />
      </section>

      <div className="content-grid">
        <section className="panel main-panel">
          <div className="panel-heading">
            <div>
              <h2>Recent Pull Requests</h2>
              <p>Latest repository development activity</p>
            </div>
            <button
              className="text-button"
              onClick={() => onSelectPR("all")}
            >
              View all →
            </button>
          </div>
          <PullRequestTable
            pullRequests={pullRequests.slice(0, 4)}
            onMerge={onMerge}
            onSelectPR={onSelectPR}
          />
        </section>

        <section className="panel activity-panel">
          <div className="panel-heading">
            <div>
              <h2>Recent Activity</h2>
              <p>Repository event stream</p>
            </div>
            <span className="live-indicator">LIVE</span>
          </div>
          <AuditTimeline events={audit.slice(0, 5)} />
        </section>
      </div>

      <div className="bottom-grid">
        <section className="panel">
          <div className="panel-heading">
            <div>
              <h2>Repository Distribution</h2>
              <p>Projects by ownership</p>
            </div>
          </div>
          <div className="repository-list">
            {repositories.map((repo) => (
              <div className="repository-item" key={repo.id}>
                <div className="repo-avatar">
                  {repo.name.substring(0, 1).toUpperCase()}
                </div>
                <div className="repo-details">
                  <strong>{repo.name}</strong>
                  <span>{repo.owner}</span>
                </div>
                <Badge type="status-neutral">{repo.visibility}</Badge>
              </div>
            ))}
          </div>
        </section>

        <section className="panel">
          <div className="panel-heading">
            <div>
              <h2>Governance Health</h2>
              <p>Current workflow conditions</p>
            </div>
          </div>
          <GovernanceHealth pullRequests={pullRequests} />
        </section>
      </div>
    </>
  );
}

function PullRequestTable({
  pullRequests,
  onMerge,
  onSelectPR,
}) {
  return (
    <div className="table-wrapper">
      <table>
        <thead>
          <tr>
            <th>PULL REQUEST</th>
            <th>AUTHOR</th>
            <th>REVIEWS</th>
            <th>CI CHECKS</th>
            <th>STATUS</th>
            <th>ACTION</th>
          </tr>
        </thead>
        <tbody>
          {pullRequests.length === 0 && (
            <tr>
              <td colSpan="6" className="empty-state">
                No Pull Requests match this filter.
              </td>
            </tr>
          )}

          {pullRequests.map((pr) => (
            <tr key={pr.id}>
              <td>
                <button
                  className="table-link"
                  onClick={() => onSelectPR(pr.id)}
                >
                  <strong>{pr.title}</strong>
                  <span>#{pr.id} · {pr.repository}</span>
                </button>
              </td>
              <td>{pr.author}</td>
              <td>
                {pr.approvals}/{pr.requiredApprovals}
              </td>
              <td>
                <Badge>{pr.checks}</Badge>
              </td>
              <td>
                <Badge>{pr.status}</Badge>
              </td>
              <td>
                {isMergeEligible(pr) ? (
                  <button
                    className="small-action"
                    onClick={() => onMerge(pr.id)}
                  >
                    Merge
                  </button>
                ) : (
                  <button
                    className="small-action secondary"
                    onClick={() => onSelectPR(pr.id)}
                  >
                    Inspect
                  </button>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function GovernanceHealth({ pullRequests }) {
  const checks = [
    {
      label: "Approval requirements",
      passed: pullRequests.filter(
        (pr) => pr.approvals >= pr.requiredApprovals
      ).length,
    },
    {
      label: "Successful CI checks",
      passed: pullRequests.filter(
        (pr) => pr.checks === "Passed"
      ).length,
    },
    {
      label: "Resolved conversations",
      passed: pullRequests.filter(
        (pr) => pr.unresolved === 0
      ).length,
    },
  ];

  return (
    <div className="health-list">
      {checks.map((item) => {
        const percentage = pullRequests.length
          ? Math.round((item.passed / pullRequests.length) * 100)
          : 0;

        return (
          <div className="health-item" key={item.label}>
            <div className="health-label">
              <span>{item.label}</span>
              <strong>{percentage}%</strong>
            </div>
            <div className="progress-track">
              <div
                className="progress-fill"
                style={{ width: `${percentage}%` }}
              />
            </div>
          </div>
        );
      })}
    </div>
  );
}

function AuditTimeline({ events }) {
  return (
    <div className="timeline">
      {events.map((event) => (
        <div className="timeline-item" key={event.id}>
          <span className={`timeline-dot ${event.type}`} />
          <div>
            <strong>{event.action}</strong>
            <p>{event.actor} · {event.target}</p>
            <span>{event.time}</span>
          </div>
        </div>
      ))}
    </div>
  );
}

function RepositoriesPage({ repositories }) {
  return (
    <section className="panel full-panel">
      <div className="panel-heading">
        <div>
          <h2>Repositories</h2>
          <p>Registered engineering projects</p>
        </div>
        <Badge type="status-success">Connected</Badge>
      </div>

      <div className="repository-list expanded">
        {repositories.map((repo) => (
          <div className="repository-item" key={repo.id}>
            <div className="repo-avatar">
              {repo.name[0].toUpperCase()}
            </div>
            <div className="repo-details">
              <strong>{repo.name}</strong>
              <span>{repo.owner} · {repo.defaultBranch}</span>
            </div>
            <Badge type="status-neutral">{repo.visibility}</Badge>
            <span className="repository-updated">{repo.updated}</span>
          </div>
        ))}
      </div>
    </section>
  );
}

function PRDetail({ pr, onClose, onApprove, onMerge }) {
  if (!pr) return null;

  const eligible = isMergeEligible(pr);

  return (
    <div className="modal-backdrop" onMouseDown={onClose}>
      <section
        className="detail-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="pr-detail-title"
        onMouseDown={(event) => event.stopPropagation()}
      >
        <div className="modal-heading">
          <div>
            <span className="eyebrow">PULL REQUEST #{pr.id}</span>
            <h2 id="pr-detail-title">{pr.title}</h2>
          </div>
          <button className="close-button" onClick={onClose}>
            ×
          </button>
        </div>

        <Badge>{pr.status}</Badge>

        <div className="branch-flow">
          <div>
            <span>FROM</span>
            <strong>{pr.source}</strong>
          </div>
          <span>→</span>
          <div>
            <span>INTO</span>
            <strong>{pr.target}</strong>
          </div>
        </div>

        <div className="detail-grid">
          <div>
            <span>Author</span>
            <strong>{pr.author}</strong>
          </div>
          <div>
            <span>Repository</span>
            <strong>{pr.repository}</strong>
          </div>
          <div>
            <span>Approvals</span>
            <strong>
              {pr.approvals}/{pr.requiredApprovals}
            </strong>
          </div>
          <div>
            <span>CI Checks</span>
            <strong>{pr.checks}</strong>
          </div>
          <div>
            <span>Unresolved discussions</span>
            <strong>{pr.unresolved}</strong>
          </div>
          <div>
            <span>Updated</span>
            <strong>{pr.updated}</strong>
          </div>
        </div>

        <div className="eligibility-box">
          <strong>
            {eligible ? "Ready for merge" : "Merge requirements not satisfied"}
          </strong>
          <p>
            {eligible
              ? "The simulated dashboard policy permits merging."
              : [
                  pr.draft && "Draft must be published",
                  pr.approvals < pr.requiredApprovals && "More approvals required",
                  pr.checks !== "Passed" && "CI checks must pass",
                  pr.unresolved > 0 && "Discussions must be resolved",
                ].filter(Boolean).join(" · ")}
          </p>
        </div>

        <div className="modal-actions">
          <button className="secondary-button" onClick={onApprove}>
            Record approval
          </button>
          <button
            className="primary-button"
            disabled={!eligible}
            onClick={() => onMerge(pr.id)}
          >
            Merge Pull Request
          </button>
        </div>
      </section>
    </div>
  );
}

function FilterBar({ filter, setFilter }) {
  return (
    <div className="filter-bar">
      {["All", "Open", "Draft", "Merged", "Closed"].map((value) => (
        <button
          key={value}
          className={`filter-button ${filter === value ? "selected" : ""}`}
          onClick={() => setFilter(value)}
        >
          {value}
        </button>
      ))}
    </div>
  );
}

function App() {
  const [active, setActive] = useState("overview");
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState("All");
  const [repositories] = useState(initialRepositories);
  const [pullRequests, setPullRequests] = useState(initialPullRequests);
  const [audit, setAudit] = useState(initialAudit);
  const [selectedPR, setSelectedPR] = useState(null);
  const [notification, setNotification] = useState("");

  const visiblePRs = useMemo(() => {
    const term = search.trim().toLowerCase();

    return pullRequests.filter((pr) => {
      const matchesSearch =
        !term ||
        [
          pr.title,
          pr.repository,
          pr.author,
          String(pr.id),
        ].some((value) => value.toLowerCase().includes(term));

      const matchesFilter =
        filter === "All" || pr.status === filter;

      return matchesSearch && matchesFilter;
    });
  }, [pullRequests, search, filter]);

  const notify = useCallback((message) => {
    setNotification(message);
    window.setTimeout(() => setNotification(""), 3000);
  }, []);

  const addAudit = useCallback((action, target, type = "info") => {
    setAudit((previous) => [
      {
        id: Date.now(),
        actor: "admin",
        action,
        target,
        time: "Just now",
        type,
      },
      ...previous,
    ]);
  }, []);

  const mergePR = useCallback((id) => {
    setPullRequests((previous) =>
      previous.map((pr) =>
        pr.id === id && isMergeEligible(pr)
          ? { ...pr, status: "Merged" }
          : pr
      )
    );

    addAudit("Pull Request merged", `PR #${id}`, "success");
    setSelectedPR(null);
    notify(`Pull Request #${id} merged.`);
  }, [addAudit, notify]);

  const approvePR = useCallback(() => {
    if (!selectedPR) return;

    setPullRequests((previous) =>
      previous.map((pr) =>
        pr.id === selectedPR.id
          ? {
              ...pr,
              approvals: Math.min(
                pr.requiredApprovals,
                pr.approvals + 1
              ),
            }
          : pr
      )
    );

    addAudit("Approval recorded", `PR #${selectedPR.id}`, "success");
    setSelectedPR((previous) => previous
      ? {
          ...previous,
          approvals: Math.min(
            previous.requiredApprovals,
            previous.approvals + 1
          ),
        }
      : null
    );

    notify("Approval recorded.");
  }, [selectedPR, addAudit, notify]);

  const selectPR = useCallback((id) => {
    if (id === null || id === "all") {
      setActive("pull-requests");
      return;
    }

    const pr = pullRequests.find((item) => item.id === id);
    setSelectedPR(pr || null);
  }, [pullRequests]);

  const content = (() => {
    switch (active) {
      case "overview":
        return (
          <Overview
            repositories={repositories}
            pullRequests={pullRequests}
            audit={audit}
            onMerge={mergePR}
            onSelectPR={selectPR}
          />
        );

      case "repositories":
        return <RepositoriesPage repositories={repositories} />;

      case "pull-requests":
        return (
          <section className="panel full-panel">
            <div className="panel-heading">
              <div>
                <h2>Pull Request Management</h2>
                <p>Review and monitor proposed repository changes.</p>
              </div>
              <Badge type="status-success">Workflow active</Badge>
            </div>
            <FilterBar filter={filter} setFilter={setFilter} />
            <PullRequestTable
              pullRequests={visiblePRs}
              onMerge={mergePR}
              onSelectPR={selectPR}
            />
          </section>
        );

      case "reviews":
        return (
          <section className="panel full-panel">
            <div className="panel-heading">
              <div>
                <h2>Code Review Management</h2>
                <p>Approval requirements and review activity.</p>
              </div>
            </div>
            <PullRequestTable
              pullRequests={visiblePRs.filter(
                (pr) => pr.status === "Open"
              )}
              onMerge={mergePR}
              onSelectPR={selectPR}
            />
          </section>
        );

      case "branches":
        return (
          <section className="panel full-panel">
            <div className="panel-heading">
              <div>
                <h2>Branch Protection</h2>
                <p>Repository-level governance controls.</p>
              </div>
            </div>
            <div className="repository-list expanded">
              {repositories.map((repo) => (
                <div className="repository-item" key={repo.id}>
                  <div className="repo-avatar">⌑</div>
                  <div className="repo-details">
                    <strong>{repo.name}/{repo.defaultBranch}</strong>
                    <span>Required reviews · CI checks · Protected branch</span>
                  </div>
                  <Badge type="status-success">Protected</Badge>
                </div>
              ))}
            </div>
          </section>
        );

      case "checks":
        return (
          <section className="panel full-panel">
            <div className="panel-heading">
              <div>
                <h2>Continuous Integration</h2>
                <p>Automated validation for proposed changes.</p>
              </div>
            </div>
            <PullRequestTable
              pullRequests={visiblePRs}
              onMerge={mergePR}
              onSelectPR={selectPR}
            />
          </section>
        );

      case "audit":
        return (
          <section className="panel full-panel">
            <div className="panel-heading">
              <div>
                <h2>Audit Logs</h2>
                <p>Recorded repository administration events.</p>
              </div>
            </div>
            <AuditTimeline events={audit} />
          </section>
        );

      default:
        return <div className="empty-state">Section unavailable.</div>;
    }
  })();

  return (
    <div className="application">
      <Sidebar active={active} setActive={setActive} />

      <main className="main-area">
        <Header
          active={active}
          search={search}
          setSearch={setSearch}
        />

        <div className="page-content">{content}</div>

        <footer className="footer">
          <span>© 2026 Nexus Engineering</span>
          <span>Repository Governance Console · Version 1.0</span>
        </footer>
      </main>

      <PRDetail
        pr={selectedPR}
        onClose={() => setSelectedPR(null)}
        onApprove={approvePR}
        onMerge={mergePR}
      />

      {notification && (
        <div className="toast" role="status">
          <span>✓</span>
          {notification}
        </div>
      )}
    </div>
  );
}

const rootElement = document.getElementById("root");

if (!rootElement) {
  throw new Error("Missing root element. Add #root to index.html.");
}

createRoot(rootElement).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
