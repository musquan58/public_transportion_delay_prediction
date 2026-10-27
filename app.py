from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "transport-delay-demo"
DB = "transport.db"

def init_db():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS predictions(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        route TEXT, source TEXT, destination TEXT, hour INTEGER,
        traffic TEXT, weather TEXT, delay INTEGER, status TEXT,
        reason TEXT, created_at TEXT)""")
        # Add username column if it does not already exist
    try:
        cur.execute("ALTER TABLE predictions ADD COLUMN username TEXT")
    except sqlite3.OperationalError:
        pass
    cur.execute("INSERT OR IGNORE INTO users(username,password) VALUES(?,?)",
                ("admin","admin123"))
    conn.commit()
    conn.close()

def predict_delay(hour, traffic, weather, route):

    delay = 3

    factors = [
        {
            "name": "Base Travel Time",
            "impact": 3,
            "icon": "🚌"
        }
    ]

    # Traffic factor
    if traffic == "Low":
        traffic_delay = 1
        factors.append({
            "name": "Low Traffic",
            "impact": traffic_delay,
            "icon": "🚦"
        })

    elif traffic == "Medium":
        traffic_delay = 5
        delay += traffic_delay
        factors.append({
            "name": "Medium Traffic",
            "impact": traffic_delay,
            "icon": "🚦"
        })

    elif traffic == "High":
        traffic_delay = 12
        delay += traffic_delay
        factors.append({
            "name": "High Traffic",
            "impact": traffic_delay,
            "icon": "🚦"
        })

    # Weather factor
    if weather == "Clear":
        weather_delay = 0

    elif weather == "Cloudy":
        weather_delay = 2
        delay += weather_delay
        factors.append({
            "name": "Cloudy Weather",
            "impact": weather_delay,
            "icon": "☁️"
        })

    elif weather == "Rainy":
        weather_delay = 8
        delay += weather_delay
        factors.append({
            "name": "Rainy Weather",
            "impact": weather_delay,
            "icon": "🌧️"
        })

    elif weather == "Storm":
        weather_delay = 15
        delay += weather_delay
        factors.append({
            "name": "Severe Weather",
            "impact": weather_delay,
            "icon": "⛈️"
        })

    # Peak hour factor
    if 7 <= hour <= 9:

        peak_delay = 7
        delay += peak_delay

        factors.append({
            "name": "Morning Peak Hour",
            "impact": peak_delay,
            "icon": "🕐"
        })

    elif 17 <= hour <= 20:

        peak_delay = 9
        delay += peak_delay

        factors.append({
            "name": "Evening Peak Hour",
            "impact": peak_delay,
            "icon": "🕐"
        })

    # Route factor
    if route in ["101", "202"]:

        route_delay = 2
        delay += route_delay

        factors.append({
            "name": "Route Congestion Factor",
            "impact": route_delay,
            "icon": "🚌"
        })

    # Determine status
    if delay <= 8:
        status = "On Time"

    elif delay <= 18:
        status = "Slight Delay"

    else:
        status = "Major Delay"

    return delay, status, factors

@app.route("/")
def home():
    return redirect(url_for("dashboard" if "user" in session else "login"))

@app.route("/register", methods=["GET","POST"])
def register():
    error = None
    success = None
    if request.method == "POST":
        username = request.form.get("username","").strip()
        password = request.form.get("password","")
        confirm = request.form.get("confirm_password","")
        if not username or not password:
            error = "Please fill all fields."
        elif password != confirm:
            error = "Passwords do not match."
        elif len(password) < 6:
            error = "Password must contain at least 6 characters."
        else:
            try:
                conn = sqlite3.connect(DB)
                conn.execute("INSERT INTO users(username,password) VALUES(?,?)",
                             (username,password))
                conn.commit()
                conn.close()
                return redirect(url_for("login", registered="1"))
            except sqlite3.IntegrityError:
                error = "Username already exists."
    return render_template("register.html", error=error, success=success)

@app.route("/forgot-password", methods=["GET","POST"])
def forgot_password():
    message = None
    if request.method == "POST":
        username = request.form.get("username","").strip()
        new_password = request.form.get("new_password","")
        confirm = request.form.get("confirm_password","")
        if not username or not new_password:
            message = "Please fill all fields."
        elif new_password != confirm:
            message = "Passwords do not match."
        elif len(new_password) < 6:
            message = "Password must contain at least 6 characters."
        else:
            conn = sqlite3.connect(DB)
            cur = conn.cursor()
            cur.execute("SELECT id FROM users WHERE username=?", (username,))
            user = cur.fetchone()
            if user:
                cur.execute("UPDATE users SET password=? WHERE username=?",
                            (new_password, username))
                conn.commit()
                conn.close()
                return redirect(url_for("login", reset="1"))
            conn.close()
            message = "Username not found."
    return render_template("forgot_password.html", message=message)

@app.route("/login", methods=["GET","POST"])
def login():
    error = None
    if request.method == "POST":
        u, p = request.form.get("username",""), request.form.get("password","")
        conn = sqlite3.connect(DB)
        user = conn.execute("SELECT username FROM users WHERE username=? AND password=?",(u,p)).fetchone()
        conn.close()
        if user:
            session["user"] = u
            return redirect(url_for("dashboard"))
        error = "Invalid username or password"
    notice = None
    if request.args.get("registered"):
        notice = "Account created successfully. You can now login."
    elif request.args.get("reset"):
        notice = "Password updated successfully. Please login."
    return render_template("login.html", error=error, notice=notice)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/dashboard")
def dashboard():
    if "user" not in session: return redirect(url_for("login"))
    return render_template("dashboard.html", username=session["user"])

@app.route("/prediction")
def prediction():
    if "user" not in session: return redirect(url_for("login"))
    return render_template("prediction.html")

@app.route("/simulator")
def simulator():
    return render_template("simulator.html")

@app.route("/statistics")
def statistics():
    if "user" not in session: return redirect(url_for("login"))
    return render_template("statistics.html")

@app.route("/history")
def history_page():
    if "user" not in session:
        return redirect(url_for("login"))

    return render_template("history.html")

@app.post("/api/predict")
def api_predict():

    if "user" not in session:
        return jsonify(error="Please login first"), 401

    data = request.get_json() or {}

    route = data.get("route", "101")
    source = data.get("source", "")
    destination = data.get("destination", "")

    traffic = data.get("traffic", "Medium")
    weather = data.get("weather", "Clear")

    try:
        hour = int(data.get("hour", 8))
    except:
        hour = 8

    # Get prediction and explanation
    delay, status, factors = predict_delay(
        hour,
        traffic,
        weather,
        route
    )

    # Create reason text for database
    reason = ", ".join(
        factor["name"] for factor in factors
        if factor["impact"] > 0
    )

    # Save prediction
    conn = sqlite3.connect(DB)

    conn.execute("""
        INSERT INTO predictions
        (route, source, destination, hour,
         traffic, weather, delay, status,
         reason, created_at,username)

        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?,?)
    """, (
        route,
        source,
        destination,
        hour,
        traffic,
        weather,
        delay,
        status,
        reason,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        session["user"]
    ))

    conn.commit()
    conn.close()

    # Send prediction + explanation to frontend
    return jsonify({

        "delay": delay,

        "status": status,

        "route": route,

        "source": source,

        "destination": destination,

        "factors": factors
    })

@app.get("/api/recent")
def recent():
    if "user" not in session: return jsonify(error="Please login first"), 401
    conn = sqlite3.connect(DB); conn.row_factory = sqlite3.Row
    rows = conn.execute("""
    SELECT route, source, destination, delay, status, created_at
    FROM predictions
    WHERE username = ?
    ORDER BY id DESC
    LIMIT 8
""", (session["user"],)).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


# =====================================
# USER PREDICTION HISTORY
# =====================================

@app.get("/api/history")
def history():

    if "user" not in session:
        return jsonify(error="Please login first"), 401

    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row

    rows = conn.execute("""
        SELECT route,
               source,
               destination,
               traffic,
               weather,
               delay,
               status,
               created_at
        FROM predictions
        WHERE username = ?
        ORDER BY id DESC
    """, (session["user"],)).fetchall()

    conn.close()

    return jsonify([dict(row) for row in rows])

@app.get("/api/stats")
def stats():
    if "user" not in session:
        return jsonify(error="Please login first"), 401

    conn = sqlite3.connect(DB)

    s = conn.execute("""
        SELECT status, COUNT(*)
        FROM predictions
        WHERE username = ?
        GROUP BY status
    """, (session["user"],)).fetchall()

    t = conn.execute("""
        SELECT traffic, COUNT(*)
        FROM predictions
        WHERE username = ?
        GROUP BY traffic
    """, (session["user"],)).fetchall()

    conn.close()

    return jsonify(
        status=dict(s),
        traffic=dict(t)
    )

@app.get("/api/analytics")
def analytics():

    if "user" not in session:
        return jsonify(error="Please login first"), 401

    username = session["user"]

    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row

    # Overall summary
    summary = conn.execute("""
        SELECT
            COUNT(*) AS total,
            AVG(delay) AS avg_delay,

            SUM(
                CASE
                    WHEN status = 'On Time' THEN 1
                    ELSE 0
                END
            ) AS on_time,

            SUM(
                CASE
                    WHEN status = 'Major Delay' THEN 1
                    ELSE 0
                END
            ) AS major_delays

        FROM predictions
        WHERE username = ?
    """, (username,)).fetchone()

    # Route analysis
    route_rows = conn.execute("""
        SELECT
            route,
            ROUND(AVG(delay), 1) AS avg_delay,
            COUNT(*) AS trips
        FROM predictions
        WHERE username = ?
        GROUP BY route
        ORDER BY avg_delay DESC
    """, (username,)).fetchall()

    # Traffic analysis
    traffic_rows = conn.execute("""
        SELECT
            traffic,
            ROUND(AVG(delay), 1) AS avg_delay,
            COUNT(*) AS trips
        FROM predictions
        WHERE username = ?
        GROUP BY traffic
    """, (username,)).fetchall()

    # Weather analysis
    weather_rows = conn.execute("""
        SELECT
            weather,
            ROUND(AVG(delay), 1) AS avg_delay,
            COUNT(*) AS trips
        FROM predictions
        WHERE username = ?
        GROUP BY weather
    """, (username,)).fetchall()

    # Status analysis
    status_rows = conn.execute("""
        SELECT
            status,
            COUNT(*) AS total
        FROM predictions
        WHERE username = ?
        GROUP BY status
    """, (username,)).fetchall()

    conn.close()

    total = int(summary["total"] or 0)
    on_time = int(summary["on_time"] or 0)
    major_delays = int(summary["major_delays"] or 0)

    on_time_percentage = (
        round((on_time / total) * 100, 1)
        if total > 0 else 0
    )

    return jsonify({

        "summary": {
            "total": total,
            "avg_delay": round(
                float(summary["avg_delay"] or 0), 1
            ),
            "on_time": on_time,
            "on_time_percentage": on_time_percentage,
            "major_delays": major_delays
        },

        "routes": [
            {
                "route": row["route"],
                "avg_delay": row["avg_delay"],
                "trips": row["trips"]
            }
            for row in route_rows
        ],

        "traffic": [
            {
                "traffic": row["traffic"],
                "avg_delay": row["avg_delay"],
                "trips": row["trips"]
            }
            for row in traffic_rows
        ],

        "weather": [
            {
                "weather": row["weather"],
                "avg_delay": row["avg_delay"],
                "trips": row["trips"]
            }
            for row in weather_rows
        ],

        "status": [
            {
                "status": row["status"],
                "total": row["total"]
            }
            for row in status_rows
        ]
    })
if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=5001)
