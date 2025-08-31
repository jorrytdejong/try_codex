# Contributing to House Finding App

## Development Workflow

### 1. Local Development Setup
```bash
# Clone and setup
git clone https://github.com/jorrytdejong/house_finding_app.git
cd house_finding_app
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Create .env file with your credentials
cp .env.example .env
# Edit .env with your actual credentials
```

### 2. Testing Changes
```bash
# Test locally first
python direct_search_selenium.py --cycles 1 --dry-run

# Test API locally
python app.py
curl http://localhost:5000/status
```

### 3. Git Workflow
```bash
# Create feature branch
git checkout -b feature/your-feature-name

# Make changes and commit
git add .
git commit -m "feat: description of your changes"

# Push and create PR
git push origin feature/your-feature-name
```

### 4. Deployment
```bash
# Deploy to Heroku after merging to main
git checkout main
git pull origin main
git push heroku main
```

## Commit Message Format
- `feat:` new feature
- `fix:` bug fix
- `docs:` documentation changes
- `refactor:` code refactoring
- `test:` adding tests
- `chore:` maintenance tasks

## Code Style
- Use meaningful variable names
- Add comments for complex logic
- Test with dry-run mode before real deployment
- Keep sensitive data in environment variables
