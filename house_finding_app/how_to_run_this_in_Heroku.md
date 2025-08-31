Good question 👌 — this script is not Flask (it’s a CLI Selenium bot), but you can still run it on Heroku. It’s not a problem, you just need to set it up differently because Heroku by default expects either:
	•	a web dyno (something that binds to $PORT, e.g. Flask, Node, Django), or
	•	a worker dyno (a long-running background process, no HTTP server).

Your script belongs to the worker category.

⸻

✅ How to run your Selenium bot on Heroku
	1.	Create a Procfile in your repo root:

worker: python house_bot.py --cycles 1

(replace house_bot.py with your actual filename)

	2.	Install Chrome + Chromedriver (Heroku doesn’t have a browser by default).
Add the Heroku buildpacks in this order:

heroku buildpacks:add --index 1 heroku/python
heroku buildpacks:add --index 2 https://github.com/heroku/heroku-buildpack-google-chrome
heroku buildpacks:add --index 3 https://github.com/heroku/heroku-buildpack-chromedriver


	3.	Tell Selenium where to find Chrome/Chromedriver
Your code already looks for GOOGLE_CHROME_BIN (set by the buildpack).
You’ll also need to point webdriver.Chrome() to CHROMEDRIVER_PATH:

self.driver = webdriver.Chrome(
    service=ChromeService(executable_path=os.environ.get("CHROMEDRIVER_PATH")),
    options=chrome_options
)

(instead of ChromeDriverManager().install() which doesn’t work on Heroku)

	4.	Dependencies: make sure requirements.txt includes:

selenium
webdriver-manager

(though on Heroku you won’t need webdriver-manager once you switch to CHROMEDRIVER_PATH).

	5.	Run on Heroku:

git push heroku main
heroku ps:scale worker=1  # start your bot
heroku logs --tail        # watch logs



⸻

⚠️ Things to keep in mind
	•	Dyno time: free Heroku plans don’t allow 24/7 scraping; worker will sleep when quota runs out.
	•	No GUI: Heroku runs headless only — you already set Chrome options for that ✅
	•	Ephemeral filesystem: JSON files (properties_data_*.json) won’t persist between dyno restarts. You’ll need external storage (e.g., AWS S3, database, or just GitHub pushes).

⸻

👉 So: it’s not a problem that it’s not Flask. Just run it as a Heroku worker dyno instead of a web app.

Do you want me to adapt your code snippet to be Heroku-ready with CHROMEDRIVER_PATH so you can just copy-paste it?