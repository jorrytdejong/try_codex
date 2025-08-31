# running one time
```bash
/Users/jorrytdejong/Documents/Ondernemersschap/house_finding_app
source .venv/bin/activate
python app.py
curl -X POST http://localhost:5000/run -H "Content-Type: application/json" -d '{"cycles":1}'
```

# Dry run (don't apply)
```bash
python direct_search_selenium.py --cycles 1 --dry-run
```