import os
import uuid
import socket
import platform
import csv
from datetime import datetime
from flask import Flask, send_file, request # type: ignore
from PIL import Image # type: ignore
import threading
import tkinter as tk
from tkinter import messagebox, filedialog

# Function to get LAN IP address
def get_lan_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))  # Connect to a public DNS server
        ip = s.getsockname()[0]  # Get the local IP address
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()
        return ip

# === CONFIG ===
STATIC_DIR = "static"
LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "access_log.txt")
CSV_FILE = os.path.join(LOG_DIR, "access_log.csv")
PORT = 8000

# === INIT APP ===
app = Flask(__name__)
os.makedirs(STATIC_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

# Storage for log data
LOG_DATA = []

# === FLASK LOGGER ===
@app.route("/track/<uid>.png")
def track(uid):
    # Collect browser fingerprint data from query params
    lang = request.args.get("lang", "unknown")
    tz = request.args.get("tz", "unknown")
    screen = request.args.get("screen", "unknown")
    plugins = request.args.get("plugins", "unknown")
    cores = request.args.get("cores", "unknown")
    memory = request.args.get("memory", "unknown")
    touch = request.args.get("touch", "unknown")
    fid = request.args.get("fid", str(uuid.uuid4()))

    log_entry = {
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "uid": uid,
        "ip": request.remote_addr,
        "user_agent": request.headers.get("User-Agent"),
        "language": lang,
        "timezone": tz,
        "screen": screen,
        "plugins": plugins,
        "cores": cores,
        "memory": memory,
        "touch": touch,
        "fid": fid
    }

    LOG_DATA.append(log_entry)

    # Log to text file
    with open(LOG_FILE, "a") as f:
        f.write(str(log_entry) + "\n")

    return send_file(f"{STATIC_DIR}/{uid}.png", mimetype="image/png")

def run_server():
    app.run(host="0.0.0.0", port=PORT)

# === GENERATE PIXEL ===
def generate_pixel():
    uid = str(uuid.uuid4())
    img_path = os.path.join(STATIC_DIR, f"{uid}.png")
    img = Image.new("RGBA", (1, 1), (0, 0, 0, 0))
    img.save(img_path)
    # Get the host IP address
    host_ip = get_lan_ip()
    print(f"[+] Pixel generated with UID: {uid}")
    print(f"[+] Embed URL: http://{host_ip}:{PORT}/track/{uid}.png")
    return uid

# === EXPORT TO CSV ===
def export_csv(file_path=CSV_FILE):
    if not LOG_DATA:
        print("[-] No data to export.")
        return
    keys = LOG_DATA[0].keys()
    with open(file_path, "w", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=keys)
        writer.writeheader()
        writer.writerows(LOG_DATA)
    print(f"[+] Logs exported to {file_path}")

# === HOST INFO ===
def get_host_info():
    info = {
        "Hostname": socket.gethostname(),
        "IP Address": get_lan_ip(),
        "MAC Address": ':'.join(['{:02x}'.format((uuid.getnode() >> ele) & 0xff)
                                 for ele in range(0, 8*6, 8)][::-1]),
        "OS": platform.platform()
    }
    print("[+] Host Info:")
    for k, v in info.items():
        print(f"   {k}: {v}")
    return info

# === GUI ===
def launch_gui():
    def on_generate():
        uid = generate_pixel()
        msg = f"Tracking Pixel UID:\n{uid}\n\nURL:\nhttp://<your-ip>:{PORT}/track/{uid}.png"
        messagebox.showinfo("Pixel Generated", msg)

    def on_start_server():
        threading.Thread(target=run_server, daemon=True).start()
        messagebox.showinfo("Server", "Tracking server started on port 8000")

    def on_show_info():
        info = get_host_info()
        msg = "\n".join([f"{k}: {v}" for k, v in info.items()])
        messagebox.showinfo("Host Info", msg)

    def on_export_csv():
        file = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
        if file:
            export_csv(file)
            messagebox.showinfo("Export", "Logs exported successfully")

    root = tk.Tk()
    root.title("Tracking Pixel Logger")
    root.geometry("300x250")

    tk.Button(root, text="Generate Pixel", command=on_generate).pack(pady=10)
    tk.Button(root, text="Start Server", command=on_start_server).pack(pady=10)
    tk.Button(root, text="Show Host Info", command=on_show_info).pack(pady=10)
    tk.Button(root, text="Export CSV", command=on_export_csv).pack(pady=10)

    root.mainloop()

# === CLI MENU ===
def cli_menu():
    while True:
        print("\n--- Tracking Pixel Logger ---")
        print("1. Generate tracking pixel")
        print("2. Start tracking server")
        print("3. Show host info")
        print("4. Export logs to CSV")
        print("5. Launch GUI")
        print("6. Exit")
        choice = input("Select option: ").strip()
        if choice == "1":
            generate_pixel()
        elif choice == "2":
            run_server()
        elif choice == "3":
            get_host_info()
        elif choice == "4":
            export_csv()
        elif choice == "5":
            launch_gui()
        elif choice == "6":
            break
        else:
            print("Invalid input.")

# === ENTRY POINT ===
if __name__ == "__main__":
    cli_menu()

# === Example JS Fingerprinting Snippet (to embed in pages) ===
"""
<script>
(function() {
    function getPlugins() {
        return Array.from(navigator.plugins).map(p => p.name).join(",");
    }
    function generateFID() {
        return Math.random().toString(36).substring(2, 12);
    }

    var img = new Image();
    img.src = "http://YOUR-IP:8000/track/PIXEL_UID.png?"
        + "lang=" + encodeURIComponent(navigator.language)
        + "&tz=" + encodeURIComponent(Intl.DateTimeFormat().resolvedOptions().timeZone)
        + "&screen=" + screen.width + "x" + screen.height
        + "&plugins=" + encodeURIComponent(getPlugins())
        + "&cores=" + navigator.hardwareConcurrency
        + "&memory=" + (navigator.deviceMemory || "unknown")
        + "&touch=" + ('ontouchstart' in window)
        + "&fid=" + generateFID();
})();
</script>
"""
