from flask import Flask, send_file, request, make_response, redirect
from datetime import datetime
import logging
import os
import uuid
from user_agents import parse as parse_ua

tracker = Flask(__name__)

# Ensure log directory exists
if not os.path.exists("logs"):
    os.makedirs("logs")

# Configure logging
logging.basicConfig(
    filename="logs/track.log",
    level=logging.INFO,
    format="%(asctime)s - %(message)s"
)

# Create a 1x1 transparent PNG if it doesn't exist
from PIL import Image
if not os.path.exists("pixel.png"):
    img = Image.new("RGBA", (1, 1), (0, 0, 0, 0))
    img.save("pixel.png")

@tracker.route("/track/<string:uid>.png")
def track(uid):
    ip = request.remote_addr
    ua_string = request.headers.get("User-Agent")
    user_agent = parse_ua(ua_string)
    referer = request.headers.get("Referer")
    timestamp = datetime.utcnow().isoformat()

    log_data = {
        "uid": uid,
        "timestamp": timestamp,
        "ip": ip,
        "browser": user_agent.browser.family,
        "os": user_agent.os.family,
        "device": user_agent.device.family,
        "referer": referer
    }

    log_line = " | ".join([f"{k}: {v}" for k, v in log_data.items()])
    logging.info(log_line)

    response = make_response(send_file("pixel.png", mimetype="image/png"))
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    return response

@tracker.route("/generate")
def generate_uid():
    uid = str(uuid.uuid4())
    pixel_url = request.host_url + f"track/{uid}.png"
    return f"<p>Use this tracking pixel URL:</p><code>{pixel_url}</code>"

if __name__ == '__main__':
    tracker.run(host='0.0.0.0', port=8000)
