#include <algorithm>
#include <iostream>
#include <map>
#include <set>
#include <stdexcept>
#include <string>
#include <vector>

enum class PRState {
    Draft,
    Open,
    Closed,
    Merged
};

enum class ReviewState {
    Commented,
    Approved,
    ChangesRequested,
    Dismissed
};

enum class CheckState {
    Pending,
    Passed,
    Failed
};

enum class MergeStrategy {
    Merge,
    Squash,
    Rebase
};

struct Commit {
    std::string sha;
    std::string message;
    std::string author;
};

struct ReviewComment {
    std::string reviewer;
    std::string file;
    int line;
    std::string body;
    bool resolved = false;
};

struct Review {
    std::string reviewer;
    ReviewState state;
    std::vector<ReviewComment> comments;
};

struct StatusCheck {
    std::string name;
    CheckState state;
};

struct BranchProtection {
    int requiredReviews = 1;
    std::set<std::string> requiredChecks;
    bool dismissStaleApprovals = true;
    bool requireConversationResolution = true;
    bool allowDirectPush = false;
    bool allowForcePush = false;
    bool requireLinearHistory = false;
};

class Branch {
private:
    std::string name_;
    std::vector<Commit> commits_;
    bool protected_ = false;

public:
    explicit Branch(std::string name) : name_(std::move(name)) {}

    const std::string& name() const {
        return name_;
    }

    void setProtected(bool value) {
        protected_ = value;
    }

    bool isProtected() const {
        return protected_;
    }

    void addCommit(const Commit& commit) {
        auto duplicate = std::find_if(
            commits_.begin(),
            commits_.end(),
            [&](const Commit& existing) {
                return existing.sha == commit.sha;
            }
        );

        if (duplicate != commits_.end()) {
            throw std::runtime_error("Duplicate commit: " + commit.sha);
        }

        commits_.push_back(commit);
    }

    const std::vector<Commit>& commits() const {
        return commits_;
    }

    std::string head() const {
        return commits_.empty() ? "" : commits_.back().sha;
    }

    void replaceCommits(const std::vector<Commit>& commits) {
        commits_ = commits;
    }
};

class PullRequest {
private:
    int number_;
    std::string title_;
    std::string source_;
    std::string target_;
    std::string author_;
    PRState state_;
    bool draft_;
    std::vector<Commit> commits_;
    std::vector<Review> reviews_;
    std::vector<ReviewComment> comments_;
    std::map<std::string, CheckState> checks_;
    std::string baseHead_;

public:
    PullRequest(
        int number,
        std::string title,
        std::string source,
        std::string target,
        std::string author,
        bool draft
    )
        : number_(number),
          title_(std::move(title)),
          source_(std::move(source)),
          target_(std::move(target)),
          author_(std::move(author)),
          state_(draft ? PRState::Draft : PRState::Open),
          draft_(draft) {}

    int number() const {
        return number_;
    }

    const std::string& title() const {
        return title_;
    }

    const std::string& source() const {
        return source_;
    }

    const std::string& target() const {
        return target_;
    }

    const std::string& author() const {
        return author_;
    }

    PRState state() const {
        return state_;
    }

    void setState(PRState state) {
        state_ = state;
    }

    bool isDraft() const {
        return draft_;
    }

    void publish() {
        draft_ = false;
        state_ = PRState::Open;
    }

    void setBaseHead(std::string head) {
        baseHead_ = std::move(head);
    }

    const std::string& baseHead() const {
        return baseHead_;
    }

    void setCommits(std::vector<Commit> commits) {
        commits_ = std::move(commits);
    }

    const std::vector<Commit>& commits() const {
        return commits_;
    }

    void addReview(const Review& review) {
        if (state_ != PRState::Open) {
            throw std::runtime_error("Reviews require an open pull request");
        }
        reviews_.push_back(review);
    }

    void addComment(const ReviewComment& comment) {
        if (comment.body.empty()) {
            throw std::runtime_error("Review comment cannot be empty");
        }
        comments_.push_back(comment);
    }

    void setCheck(const std::string& name, CheckState state) {
        checks_[name] = state;
    }

    const std::vector<Review>& reviews() const {
        return reviews_;
    }

    std::vector<Review>& reviews() {
        return reviews_;
    }

    const std::vector<ReviewComment>& comments() const {
        return comments_;
    }

    std::vector<ReviewComment>& comments() {
        return comments_;
    }

    const std::map<std::string, CheckState>& checks() const {
        return checks_;
    }
};

struct EligibilityResult {
    bool eligible;
    std::vector<std::string> reasons;
};

class Repository {
private:
    std::string name_;
    std::map<std::string, Branch> branches_;
    std::map<int, PullRequest> pullRequests_;
    std::map<std::string, BranchProtection> protection_;
    int nextPR_ = 1;

public:
    explicit Repository(std::string name) : name_(std::move(name)) {}

    Branch& createBranch(
        const std::string& name,
        const std::string& from = ""
    ) {
        if (branches_.contains(name)) {
            throw std::runtime_error("Branch already exists: " + name);
        }

        Branch branch(name);

        if (!from.empty()) {
            auto base = branches_.find(from);
            if (base == branches_.end()) {
                throw std::runtime_error("Unknown base branch: " + from);
            }

            branch.replaceCommits(base->second.commits());
        }

        auto [iterator, inserted] =
            branches_.emplace(name, std::move(branch));

        return iterator->second;
    }

    Branch& branch(const std::string& name) {
        auto iterator = branches_.find(name);
        if (iterator == branches_.end()) {
            throw std::runtime_error("Unknown branch: " + name);
        }
        return iterator->second;
    }

    void configureProtection(
        const std::string& branchName,
        BranchProtection policy
    ) {
        Branch& target = branch(branchName);
        target.setProtected(true);
        protection_[branchName] = std::move(policy);
    }

    PullRequest& createPullRequest(
        const std::string& title,
        const std::string& source,
        const std::string& target,
        const std::string& author,
        bool draft = false
    ) {
        Branch& sourceBranch = branch(source);
        Branch& targetBranch = branch(target);

        if (source == target) {
            throw std::runtime_error("Source and target cannot match");
        }

        PullRequest pr(
            nextPR_++,
            title,
            source,
            target,
            author,
            draft
        );

        pr.setCommits(sourceBranch.commits());
        pr.setBaseHead(targetBranch.head());

        auto [iterator, inserted] =
            pullRequests_.emplace(pr.number(), std::move(pr));

        return iterator->second;
    }

    EligibilityResult evaluateMerge(
        const PullRequest& pr
    ) const {
        EligibilityResult result{true, {}};

        if (pr.state() != PRState::Open) {
            result.eligible = false;
            result.reasons.push_back("Pull request is not open");
        }

        if (pr.isDraft()) {
            result.eligible = false;
            result.reasons.push_back("Pull request is still a draft");
        }

        if (pr.commits().empty()) {
            result.eligible = false;
            result.reasons.push_back("Pull request has no commits");
        }

        auto policyIterator = protection_.find(pr.target());

        if (policyIterator == protection_.end()) {
            return result;
        }

        const BranchProtection& policy = policyIterator->second;

        std::set<std::string> approvedReviewers;

        for (const Review& review : pr.reviews()) {
            if (review.state == ReviewState::Approved &&
                review.reviewer != pr.author()) {
                approvedReviewers.insert(review.reviewer);
            }

            if (review.state == ReviewState::ChangesRequested) {
                result.eligible = false;
                result.reasons.push_back(
                    "A reviewer has requested changes"
                );
            }
        }

        if (static_cast<int>(approvedReviewers.size()) <
            policy.requiredReviews) {
            result.eligible = false;
            result.reasons.push_back(
                "Required approvals have not been satisfied"
            );
        }

        for (const std::string& required : policy.requiredChecks) {
            auto check = pr.checks().find(required);

            if (check == pr.checks().end() ||
                check->second != CheckState::Passed) {
                result.eligible = false;
                result.reasons.push_back(
                    "Required status check failed or is missing: " +
                    required
                );
            }
        }

        if (policy.requireConversationResolution) {
            const auto unresolved = std::any_of(
                pr.comments().begin(),
                pr.comments().end(),
                [](const ReviewComment& comment) {
                    return !comment.resolved;
                }
            );

            if (unresolved) {
                result.eligible = false;
                result.reasons.push_back(
                    "Unresolved review conversations remain"
                );
            }
        }

        return result;
    }

    void merge(
        PullRequest& pr,
        MergeStrategy strategy
    ) {
        EligibilityResult result = evaluateMerge(pr);

        if (!result.eligible) {
            std::string message = "Merge blocked:";
            for (const auto& reason : result.reasons) {
                message += " " + reason + ";";
            }
            throw std::runtime_error(message);
        }

        Branch& target = branch(pr.target());

        if (strategy == MergeStrategy::Squash) {
            target.addCommit({
                "squash-" + std::to_string(pr.number()),
                "Squash merge PR #" +
                    std::to_string(pr.number()) +
                    ": " + pr.title(),
                pr.author()
            });
        } else if (strategy == MergeStrategy::Merge) {
            target.addCommit({
                "merge-" + std::to_string(pr.number()),
                "Merge PR #" +
                    std::to_string(pr.number()) +
                    ": " + pr.title(),
                pr.author()
            });
        } else {
            for (const auto& commit : pr.commits()) {
                target.addCommit({
                    "rebased-" + commit.sha,
                    commit.message,
                    commit.author
                });
            }
        }

        pr.setState(PRState::Merged);
    }

    void directPush(
        const std::string& branchName,
        const std::vector<Commit>& commits
    ) {
        Branch& target = branch(branchName);

        auto policy = protection_.find(branchName);

        if (target.isProtected() &&
            policy != protection_.end() &&
            !policy->second.allowDirectPush) {
            throw std::runtime_error(
                "Direct push to protected branch is blocked"
            );
        }

        for (const auto& commit : commits) {
            target.addCommit(commit);
        }
    }

    Repository clone() const {
        Repository copy(name_);

        for (const auto& [name, branch] : branches_) {
            Branch cloned(name);
            cloned.replaceCommits(branch.commits());
            cloned.setProtected(branch.isProtected());
            copy.branches_.emplace(name, std::move(cloned));
        }

        copy.protection_ = protection_;
        return copy;
    }

    void pullFrom(
        const Repository& remote,
        const std::string& branchName
    ) {
        const Branch& remoteBranch =
            remote.branch(branchName);

        Branch& localBranch = branch(branchName);
        localBranch.replaceCommits(remoteBranch.commits());
    }

    void printState() const {
        std::cout << "\nRepository: " << name_ << "\n";

        for (const auto& [name, branch] : branches_) {
            std::cout
                << "  " << name
                << " head=" << branch.head()
                << " protected=" << std::boolalpha
                << branch.isProtected()
                << " commits=" << branch.commits().size()
                << "\n";
        }
    }
};

int main() {
    try {
        Repository remote("security-platform");

        Branch& mainBranch = remote.createBranch("main");

        mainBranch.addCommit({
            "a1",
            "Initial repository implementation",
            "alice"
        });

        remote.configureProtection(
            "main",
            BranchProtection{
                2,
                {"tests", "security-scan"},
                true,
                true,
                false,
                false,
                true
            }
        );

        Repository local = remote.clone();

        local.createBranch("feature/remote-workflow", "main");

        local.branch("feature/remote-workflow").addCommit({
            "b1",
            "Document clone pull and push behavior",
            "bob"
        });

        local.branch("feature/remote-workflow").addCommit({
            "b2",
            "Document README and issue workflow",
            "bob"
        });

        PullRequest& pr = remote.createPullRequest(
            "Document remote repository workflow",
            "feature/remote-workflow",
            "main",
            "bob"
        );

        pr.addComment({
            "carol",
            "README.md",
            40,
            "Explain why protected branches reject direct pushes.",
            false
        });

        pr.addReview({
            "carol",
            ReviewState::Approved,
            {}
        });

        pr.addReview({
            "david",
            ReviewState::Approved,
            {}
        });

        pr.setCheck("tests", CheckState::Passed);
        pr.setCheck("security-scan", CheckState::Passed);

        EligibilityResult before =
            remote.evaluateMerge(pr);

        std::cout
            << "Eligible before resolving comments: "
            << std::boolalpha
            << before.eligible
            << "\n";

        for (auto& comment : pr.comments()) {
            comment.resolved = true;
        }

        EligibilityResult after =
            remote.evaluateMerge(pr);

        std::cout
            << "Eligible after resolving comments: "
            << after.eligible
            << "\n";

        if (after.eligible) {
            remote.merge(pr, MergeStrategy::Squash);
        }

        try {
            local.branch("main").addCommit({
                "unauthorized",
                "Attempt direct protected push",
                "eve"
            });

            remote.directPush(
                "main",
                {local.branch("main").commits().back()}
            );
        } catch (const std::exception& error) {
            std::cout
                << "Expected protection failure: "
                << error.what()
                << "\n";
        }

        local.pullFrom(remote, "main");

        if (local.branch("main").head() !=
            remote.branch("main").head()) {
            throw std::runtime_error(
                "Pull synchronization failed"
            );
        }

        remote.printState();

        std::cout
            << "\nRepository governance workflow completed.\n";

    } catch (const std::exception& error) {
        std::cerr
            << "Fatal error: "
            << error.what()
            << "\n";
        return 1;
    }

    return 0;
}
