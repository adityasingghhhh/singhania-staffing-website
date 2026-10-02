from flask import (
    Flask,
    render_template,
    request,
    jsonify,
    redirect,
    session,
    send_from_directory
)

import sqlite3
from datetime import datetime
import os


# =========================================================
# FLASK APP
# =========================================================

app = Flask(__name__)

app.secret_key = "singhania_secret_key_2026"


# =========================================================
# DATABASE
# =========================================================

def get_db():
    conn = sqlite3.connect("attendance.db")
    conn.row_factory = sqlite3.Row
    return conn


def init_db():

    conn = get_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            hotel TEXT NOT NULL,
            date TEXT NOT NULL,
            arrival_time TEXT,
            leaving_time TEXT,
            latitude TEXT,
            longitude TEXT
        )
    """)

    conn.commit()

    # Check existing columns
    columns = [
        row["name"]
        for row in conn.execute(
            "PRAGMA table_info(attendance)"
        ).fetchall()
    ]

    # Add latitude if missing
    if "latitude" not in columns:
        conn.execute(
            "ALTER TABLE attendance ADD COLUMN latitude TEXT"
        )

    # Add longitude if missing
    if "longitude" not in columns:
        conn.execute(
            "ALTER TABLE attendance ADD COLUMN longitude TEXT"
        )

    conn.commit()
    conn.close()


# Create database automatically
init_db()


# =========================================================
# PWA SERVICE WORKER
# =========================================================

@app.route("/sw.js")
def service_worker():

    return send_from_directory(
        os.path.join(app.root_path, "static"),
        "sw.js",
        mimetype="application/javascript"
    )


# =========================================================
# HOME PAGE
# =========================================================

@app.route("/")
def home():

    return render_template("index.html")


# =========================================================
# ADMIN LOGIN
# =========================================================

@app.route("/admin-login", methods=["GET", "POST"])
def admin_login():

    if request.method == "POST":

        username = request.form.get(
            "username", ""
        ).strip()

        password = request.form.get(
            "password", ""
        ).strip()

        # Admin credentials
        if username == "Prashant" and password == "Prashant@123":

            session["admin"] = True

            return redirect("/admin")

        return render_template(
            "admin_login.html",
            error="Invalid username or password"
        )

    return render_template("admin_login.html")


# =========================================================
# WAITER LOGIN
# =========================================================

@app.route("/waiter-login", methods=["GET", "POST"])
def waiter_login():

    if request.method == "POST":

        username = request.form.get(
            "username", ""
        ).strip()

        password = request.form.get(
            "password", ""
        ).strip()

        # Simple waiter login
        if username and password:

            session["waiter_name"] = username

            return redirect("/waiter")

        return render_template(
            "waiter_login.html",
            error="Please enter username and password"
        )

    return render_template("waiter_login.html")


# =========================================================
# WAITER ATTENDANCE PAGE
# =========================================================

@app.route("/waiter")
def waiter():

    if "waiter_name" not in session:

        return redirect("/waiter-login")

    return render_template(
        "waiter.html",
        name=session["waiter_name"]
    )


# =========================================================
# ARRIVAL
# =========================================================

@app.route("/arrive", methods=["POST"])
def arrive():

    try:

        data = request.get_json()

        if not data:

            return jsonify({
                "success": False,
                "message": "No data received."
            })


        name = data.get(
            "name", ""
        ).strip()

        hotel = data.get(
            "hotel", ""
        ).strip()

        latitude = data.get("latitude")

        longitude = data.get("longitude")


        # Check name and hotel
        if not name or not hotel:

            return jsonify({
                "success": False,
                "message": "Please enter your name and hotel name."
            })


        # Location verification
        if latitude is None or longitude is None:

            return jsonify({
                "success": False,
                "message": "Please verify your location first."
            })


        # Current date and time
        now = datetime.now()

        date = now.strftime("%Y-%m-%d")

        arrival_time = now.strftime(
            "%I:%M:%S %p"
        )


        conn = get_db()


        # Check if already working
        existing = conn.execute("""
            SELECT id
            FROM attendance
            WHERE name = ?
            AND hotel = ?
            AND date = ?
            AND arrival_time IS NOT NULL
            AND leaving_time IS NULL
            ORDER BY id DESC
            LIMIT 1
        """, (
            name,
            hotel,
            date
        )).fetchone()


        if existing:

            conn.close()

            return jsonify({
                "success": False,
                "message": "You have already marked arrival."
            })


        # Save attendance
        conn.execute("""
            INSERT INTO attendance
            (
                name,
                hotel,
                date,
                arrival_time,
                latitude,
                longitude
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            name,
            hotel,
            date,
            arrival_time,
            str(latitude),
            str(longitude)
        ))


        conn.commit()

        conn.close()


        return jsonify({
            "success": True,
            "message": "Arrival marked successfully."
        })


    except Exception as e:

        print("ARRIVAL ERROR:", e)

        return jsonify({
            "success": False,
            "message": "Something went wrong while marking arrival."
        })


# =========================================================
# LEAVING
# =========================================================

@app.route("/leave", methods=["POST"])
def leave():

    try:

        data = request.get_json()

        if not data:

            return jsonify({
                "success": False,
                "message": "No data received."
            })


        name = data.get(
            "name", ""
        ).strip()

        hotel = data.get(
            "hotel", ""
        ).strip()


        if not name or not hotel:

            return jsonify({
                "success": False,
                "message": "Please enter your name and hotel name."
            })


        now = datetime.now()

        date = now.strftime("%Y-%m-%d")

        leaving_time = now.strftime(
            "%I:%M:%S %p"
        )


        conn = get_db()


        # Find today's active attendance
        record = conn.execute("""
            SELECT id
            FROM attendance
            WHERE name = ?
            AND hotel = ?
            AND date = ?
            AND arrival_time IS NOT NULL
            AND leaving_time IS NULL
            ORDER BY id DESC
            LIMIT 1
        """, (
            name,
            hotel,
            date
        )).fetchone()


        if not record:

            conn.close()

            return jsonify({
                "success": False,
                "message": "No active arrival found."
            })


        # Save leaving time
        conn.execute("""
            UPDATE attendance
            SET leaving_time = ?
            WHERE id = ?
        """, (
            leaving_time,
            record["id"]
        ))


        conn.commit()

        conn.close()


        return jsonify({
            "success": True,
            "message": "Leaving time marked successfully."
        })


    except Exception as e:

        print("LEAVING ERROR:", e)

        return jsonify({
            "success": False,
            "message": "Something went wrong while marking leaving."
        })


# =========================================================
# ADMIN DASHBOARD
# =========================================================

@app.route("/admin")
def admin():

    # Check admin login
    if not session.get("admin"):

        return redirect("/admin-login")


    conn = get_db()


    # All attendance records
    records = conn.execute("""
        SELECT *
        FROM attendance
        ORDER BY id DESC
    """).fetchall()


    # Total attendance
    total = conn.execute("""
        SELECT COUNT(*)
        FROM attendance
    """).fetchone()[0]


    # Present
    present = conn.execute("""
        SELECT COUNT(*)
        FROM attendance
        WHERE arrival_time IS NOT NULL
    """).fetchone()[0]


    # Currently working
    working = conn.execute("""
        SELECT COUNT(*)
        FROM attendance
        WHERE arrival_time IS NOT NULL
        AND leaving_time IS NULL
    """).fetchone()[0]


    conn.close()


    return render_template(
        "admin.html",
        records=records,
        total=total,
        present=present,
        working=working
    )


# =========================================================
# LOGOUT
# =========================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect("/")


# =========================================================
# RUN APPLICATION
# =========================================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )