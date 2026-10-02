import threading
import time
import webview

from app import app


def start_flask():
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=False,
        use_reloader=False
    )


# Start Flask server
server_thread = threading.Thread(
    target=start_flask,
    daemon=True
)

server_thread.start()

# Wait for Flask to start
time.sleep(2)

# Open app window
webview.create_window(
    "Singhania Staff Attendance",
    "http://127.0.0.1:5000",
    width=1200,
    height=800,
    resizable=True
)

webview.start()