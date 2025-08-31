# Git Workflow for Feature Development

## Step-by-Step Feature Implementation Workflow

### 1. **Start with a Clean Main Branch**
```bash
# Always start from main and make sure it's up to date
git checkout main
git pull origin main
```

### 2. **Create a Feature Branch**
```bash
# Branch naming convention: feature/JIRA-123-short-description
git checkout -b feature/HFA-001-implement-room-filtering

# For different types of work:
git checkout -b feature/HFA-123-add-notifications
git checkout -b bugfix/HFA-456-fix-login-timeout  
git checkout -b hotfix/HFA-789-critical-security-fix
```

### 3. **Work on Your Feature**
```bash
# Make your changes
# Test locally: python direct_search_selenium.py --cycles 1 --dry-run

# Commit frequently with descriptive messages
git add .
git commit -m "feat(filtering): add room count detection logic

- Parse room count from listing descriptions
- Skip listings with only 1 room
- Add unit tests for room parsing
- Refs: HFA-001"

# Continue working...
git commit -m "feat(filtering): add student housing detection

- Check for 'studenten' keyword in descriptions
- Skip student-only listings
- Refs: HFA-001"
```

### 4. **Keep Your Branch Updated**
```bash
# Regularly sync with main to avoid conflicts
git checkout main
git pull origin main
git checkout feature/HFA-001-implement-room-filtering
git merge main  # or git rebase main for cleaner history
```

### 5. **Push and Create Pull Request**
```bash
# Push your feature branch
git push origin feature/HFA-001-implement-room-filtering

# Then go to GitHub and create a Pull Request
# Link it to your Jira ticket: "Closes HFA-001" in the PR description
```

### 6. **Review and Deploy**
```bash
# After PR is approved and merged:
git checkout main
git pull origin main
git branch -d feature/HFA-001-implement-room-filtering  # Clean up local branch

# Deploy to production
git push heroku main
```

## Jira Integration Tips

### **Commit Message Format**
```bash
git commit -m "feat(scope): description

- Bullet point of what changed
- Another change
- Refs: HFA-123"  # Links to Jira ticket
```

### **Branch Naming Convention**
- `feature/HFA-123-short-description` - New features
- `bugfix/HFA-456-fix-something` - Bug fixes  
- `hotfix/HFA-789-urgent-fix` - Critical production fixes
- `chore/HFA-101-update-deps` - Maintenance tasks

### **Pull Request Template**
```markdown
## Changes
- List what you implemented
- Reference the requirements

## Testing
- [ ] Tested locally with dry-run
- [ ] No linting errors
- [ ] API endpoints work

## Jira
Closes HFA-123

## Checklist
- [ ] Code follows style guidelines
- [ ] Tests added/updated
- [ ] Documentation updated
```

## Common Commands Quick Reference

```bash
# See all branches
git branch -a

# Switch between branches
git checkout feature/my-feature
git checkout main

# See what changed
git status
git diff
git log --oneline -5

# Undo changes (be careful!)
git reset --hard HEAD~1  # Undo last commit
git checkout -- filename  # Undo file changes

# Clean up merged branches
git branch --merged | grep -v main | xargs git branch -d
```
