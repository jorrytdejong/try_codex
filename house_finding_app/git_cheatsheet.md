# 📖 Git Commands Cheat Sheet

A curated list of useful Git commands and workflows.

---

## 🔍 Repository Checks

```bash
# Check if you're in a Git repo
git status

# Look for .git directory
ls -a
```

# 🌱 Branching

```bash
# Start from main branch
git checkout main
git pull origin main

# Create and switch to a new feature branch
git checkout -b feature/HFA-001-room-filtering

# Other branch naming conventions
git checkout -b bugfix/HFA-456-fix-login-timeout
git checkout -b hotfix/HFA-789-critical-security-fix
git checkout -b chore/HFA-101-update-deps
```

# 💾 Staging & Committing

```bash
# Stage all changes
git add .

# Commit with a Conventional Commit message
git commit -m "feat(filtering): add room count detection logic"
git commit -m "fix(api): handle login timeout"
git commit -m "docs: update contributing guidelines"
git commit -m "refactor: simplify filtering logic"
```

# 🔗 Linking Commits to Jira Tickets

```bash
# Example with Jira ticket HFA-001
git commit -m "feat(filtering): add student housing detection (HFA-001)"

# Example with multiple tickets
git commit -m "fix(auth): handle login edge cases (HFA-002, HFA-003)"
```
# ⬆️ Pushing & Pull Requests
```bash
# Push feature branch to remote
git push origin feature/HFA-001-room-filtering

# After merge, clean up branch
git checkout main
git pull origin main
git branch -d feature/HFA-001-room-filtering
```

# 🖥️ Merge a branch into main
```bash
# 1. Switch to main
git checkout main

# 2. Make sure main is up to date
git pull origin main

# 3. Merge the branch into main
git merge feature/my-feature

# 4. Push the updated main branch to GitHub
git push origin main
```

# 🔄 Syncing with Main
```bash
# Merge latest main into your branch
git checkout main
git pull origin main
git checkout feature/HFA-001-room-filtering
git merge main

# OR use rebase for cleaner history
git rebase main
```

# 🕵️ Inspecting Repo
```bash
# See all branches
git branch -a

# See last 5 commits (one-line format)
git log --oneline -5

# See unstaged changes
git diff
```

# 🧹 Cleaning Up
```bash
# Undo last commit (careful!)
git reset --hard HEAD~1

# Undo file changes
git checkout -- filename

# Delete all merged branches except main
git branch --merged | grep -v main | xargs git branch -d

# Delete branch safely (only if already merged into main)
git branch -d feature/my-feature

# Force delete (even if not merged)
git branch -D feature/my-feature
```

# 🚀 Deployment
```bash
# Push to GitHub
git push origin main

# Deploy to Heroku
git push heroku main
```

# 🏷️ Tags & Releases
```bash
# Create a version tag
git tag v1.0.0

# Push tags to remote
git push origin --tags
```

# ✅ Commit Message Types (Conventional Commits)
	•	feat: → New feature
	•	fix: → Bug fix
	•	docs: → Documentation only
	•	style: → Formatting (no logic change)
	•	refactor: → Code restructuring (no new feature/fix)
	•	test: → Adding/updating tests
	•	chore: → Maintenance tasks
	•	perf: → Performance improvements
	•	ci: → CI/CD changes
	•	build: → Build system/dependencies
	•	revert: → Revert a commit

## Examples
```bash
# 🆕 New feature
git commit -m "feat(filtering): skip listings with only 1 room (HFA-001)"

# 🐛 Bug fix
git commit -m "fix(api): correct login timeout handling (HFA-002)"

# 📚 Documentation
git commit -m "docs(readme): add instructions for Heroku deployment"

# 🎨 Style / formatting (no logic changes)
git commit -m "style(code): reformat search function with black"

# 🔨 Refactor (improve structure, same functionality)
git commit -m "refactor(scraper): extract filtering logic into helper function"

# 🧪 Tests
git commit -m "test(filtering): add unit tests for student housing detection"

# 🔧 Chore (maintenance work)
git commit -m "chore(deps): update selenium to latest version"

# 🚀 Performance improvement
git commit -m "perf(scraper): optimize loop to reduce memory usage"

# 🔁 CI/CD pipeline
git commit -m "ci(heroku): add workflow for automatic deployment on merge"

# 🏗️ Build system / dependencies
git commit -m "build(pip): lock dependency versions in requirements.txt"

# ↩️ Revert
git commit -m "revert: undo room filtering due to false positives (HFA-003)"
```