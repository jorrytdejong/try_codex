Short answer: yes, but not literally “forever” on Heroku. Dynos are restarted at least once every 24 hours and the filesystem is ephemeral. You can still run continuously with auto-restart, but you must handle persistence and restarts.

What to do
- Use a worker dyno for the long-running loop (recommended).
- Persist state off-dyno (S3, Postgres) or accept losing JSON files on restart.
- Add reasonable sleeps between cycles to avoid memory spikes/blocks.
- Auto-resume after dyno restarts.

Minimal setup
1) Add a worker process
- Procfile:
  web: gunicorn app:app
  worker: python -u runner.py
- runner.py:
  from time import sleep
  from direct_search_selenium import HouseBot

  if __name__ == "__main__":
      while True:
          try:
              bot = HouseBot()
              bot.run()  # one cycle
          except Exception:
              pass
          sleep(300)  # pause 5 min between cycles

2) Scale worker
- heroku ps:scale worker=1
- Keep web dyno for API: heroku ps:scale web=1

3) Persistence
- If you want history across restarts, push results to S3 or Postgres instead of writing JSON to disk.

Notes
- Background thread in the web dyno works, but worker dyno is more reliable.
- Heroku daily restarts will interrupt the loop; the worker will auto-continue after restart.
- Chrome must stay headless on Heroku.