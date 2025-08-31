from flask import Flask, request, jsonify
import threading
import time
from direct_search_selenium import HouseBot
import os
import json

app = Flask(__name__)


STATUS_FILE = "task_status.json"

DEFAULT_STATUS = {
    "running": False,
    "started_at": None,
    "cycles": 0,
    "hours": None,
    "stop_requested": False,
}


def load_status() -> dict:
    """Load the current task status from disk.

    If the status file does not exist or is malformed, a default status is
    returned and written to disk so future calls operate on a valid file.
    """
    if not os.path.exists(STATUS_FILE):
        save_status(DEFAULT_STATUS.copy())
        return DEFAULT_STATUS.copy()
    try:
        with open(STATUS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        # If the file cannot be read/parsed, reset to default to avoid crashes
        save_status(DEFAULT_STATUS.copy())
        return DEFAULT_STATUS.copy()


def save_status(status: dict) -> None:
    """Persist the provided status dictionary atomically to disk."""
    tmp_path = STATUS_FILE + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(status, f)
    os.replace(tmp_path, STATUS_FILE)


# Ensure the status file exists at import time
load_status()
def _run_bot(cycles: int = 1, hours: float | None = None):
    """Background thread target that executes the scraper."""
    status = load_status()
    status.update(
        {
            "running": True,
            "started_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "cycles": cycles,
            "hours": hours,
            "stop_requested": False,
        }
    )
    save_status(status)

    executed = 0
    start_ts = time.time()
    try:
        while True:
            status = load_status()
            if status["stop_requested"]:
                print("Job stopped by user request")
                break
            if cycles and executed >= cycles:
                break
            if hours and (time.time() - start_ts) / 3600 >= hours:
                break
            bot = HouseBot(headless=True)  # Force headless for server API
            bot.run()
            executed += 1
    finally:
        status = load_status()
        status["running"] = False
        status["stop_requested"] = False
        save_status(status)


@app.route("/run", methods=["POST"])
def run_endpoint():
    """Start a scraping job. JSON body may contain {cycles:int, hours:float}."""
    status = load_status()
    if status["running"]:
        return jsonify({"status": "busy", "message": "A job is already running"}), 409

    data = request.get_json() or {}
    cycles = int(data.get("cycles", 1))
    hours = data.get("hours")
    if hours is not None:
        hours = float(hours)

    status.update({
        "running": True,
        "started_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "cycles": cycles,
        "hours": hours,
        "stop_requested": False,
    })
    save_status(status)
    thread = threading.Thread(target=_run_bot, args=(cycles, hours), daemon=True)
    thread.start()
    return jsonify({"status": "started", "cycles": cycles, "hours": hours})


@app.route("/stop", methods=["POST"])
def stop_endpoint():
    """Stop the currently running scraping job."""
    status = load_status()
    if not status["running"]:
        return jsonify({"status": "not_running", "message": "No job is currently running"}), 400

    status["stop_requested"] = True
    save_status(status)
    return jsonify({"status": "stop_requested", "message": "Stop signal sent to running job"})


@app.route("/status", methods=["GET"])
def status_endpoint():
    """Return info about the current/background task."""
    status = load_status()
    return jsonify(status)


@app.route("/processed-houses", methods=["GET"])
def processed_houses_endpoint():
    """Return the list of houses from the most recent properties_data_*.json file."""
    try:
        # Find the most recent properties_data_*.json file
        import glob
        property_files = glob.glob("properties_data_*.json")
        if property_files:
            # Sort by filename (timestamp) to get the most recent
            most_recent_file = max(property_files)
            with open(most_recent_file, "r", encoding="utf-8") as f:
                houses_data = json.load(f)
            return jsonify({
                "count": len(houses_data),
                "houses": houses_data,
                "source_file": most_recent_file
            })
        else:
            return jsonify({
                "count": 0,
                "houses": {},
                "message": "No properties data files found"
            })
    except Exception as e:
        return jsonify({
            "error": f"Failed to read properties data: {str(e)}"
        }), 500


@app.route("/processed-houses/list", methods=["GET"])
def processed_houses_list_endpoint():
    """Return a simple list of house street names from the most recent scrape."""
    try:
        # Find the most recent properties_data_*.json file
        import glob
        property_files = glob.glob("properties_data_*.json")
        if property_files:
            # Sort by filename (timestamp) to get the most recent
            most_recent_file = max(property_files)
            with open(most_recent_file, "r", encoding="utf-8") as f:
                houses_data = json.load(f)
            
            street_names = []
            for house_key, house_data in houses_data.items():
                name = house_data.get('name', 'Unknown address')
                # Check if this house has processing info (success/failure)
                success = house_data.get('success')
                if success is not None:
                    status = "✅" if success else "❌"
                    street_names.append(f"{status} {name}")
                else:
                    # Raw scraped data without processing info
                    street_names.append(f"⏳ {name}")
            
            return jsonify({
                "count": len(street_names),
                "streets": street_names,
                "source_file": most_recent_file
            })
        else:
            return jsonify({
                "count": 0,
                "streets": [],
                "message": "No properties data files found"
            })
    except Exception as e:
        return jsonify({
            "error": f"Failed to read properties data: {str(e)}"
        }), 500


@app.route("/")
def root():
    return "HouseBot scraper – use /run to start, /stop to quit, /status to check, /processed-houses for latest data, /processed-houses/list for simple list."


if __name__ == "__main__":
    # Useful for local testing – on Heroku gunicorn will run it.
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000))) 