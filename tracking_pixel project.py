from flask import Flask, request, send_file, make_response
from datetime import datetime, timezone
import logging
import os
import uuid
from user_agents import parse as parse_ua
from PIL import Image

# --- App Setup ---
tracker = Flask(__name__)
LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "track.log")
PIXEL_FILE = "pixel.png"

# --- Ensure log directory exists ---
os.makedirs(LOG_DIR, exist_ok=True)

# --- Configure logging ---
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s - %(message)s"
)

# --- Create transparent 1x1 PNG if not exists ---
if not os.path.exists(PIXEL_FILE):
    img = Image.new("RGBA", (1, 1), (0, 0, 0, 0))
    img.save(PIXEL_FILE)

# --- Tracking route ---
@tracker.route("/track/<string:uid>.png")
def track(uid):
    ip = request.remote_addr
    ua_string = request.headers.get("User-Agent", "Unknown")
    referer = request.headers.get("Referer", "None")
    timestamp = datetime.now(timezone.utc).isoformat()

    user_agent = parse_ua(ua_string)
    log_entry = (
        f"UID: {uid} | Time: {timestamp} | IP: {ip} | "
        f"Browser: {user_agent.browser.family} {user_agent.browser.version_string} | "
        f"OS: {user_agent.os.family} {user_agent.os.version_string} | "
        f"Device: {user_agent.device.family} | Referer: {referer} | UA: {ua_string}"
    )

    logging.info(log_entry)

    response = make_response(send_file(PIXEL_FILE, mimetype="image/png"))
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    return response

# --- UID generator ---
@tracker.route("/generate")
def generate_uid():
    uid = str(uuid.uuid4())
    pixel_url = request.host_url + f"track/{uid}.png"
    return f"<p>Use this tracking pixel URL:</p><code>{pixel_url}</code>"

# --- Run the server ---
if __name__ == '__main__':
    tracker.run(host='0.0.0.0', port=8000)
