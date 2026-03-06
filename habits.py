from flask import Flask, render_template, request, redirect, jsonify, session, g, flash
from supabase import create_client
import os
import threading
from cachetools import TTLCache
from dotenv import load_dotenv
from datetime import datetime
from zoneinfo import ZoneInfo

load_dotenv()

app = Flask(__name__)

app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=True,
)

app.secret_key = os.getenv("SECRET_KEY")

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_ANON_KEY")
)

# In-memory cache for index page habits data, avoids hitting supabase on every load
# Key: (user_id, date_iso), TTL 5 min, invalidated on save or create-habit
_index_cache = TTLCache(maxsize=500, ttl=300)
_index_cache_lock = threading.Lock()

# Cache for auth user lookup, reduces supabase auth API calls (one per token per 5 min)
_user_cache = TTLCache(maxsize=500, ttl=300)
_user_cache_lock = threading.Lock()


# return habits + today's status from cache or supabase
def get_index_habits(user_id: str, today: str) -> list:
    key = (user_id, today)
    with _index_cache_lock:
        if key in _index_cache:
            return _index_cache[key]
    rows = (
        supabase
        .table("habits")
        .select("id,name,daily_habits(completed)")
        .eq("user_id", user_id)
        .eq("daily_habits.log_date", today)
        .order("created_at")
        .execute()
        .data
    )
    with _index_cache_lock:
        _index_cache[key] = rows
    return rows


# Clear cached index data so next load refetches from supabase
def invalidate_index_cache(user_id: str, today: str) -> None:
    key = (user_id, today)
    with _index_cache_lock:
        _index_cache.pop(key, None)


# login page
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        res = supabase.auth.sign_in_with_password({
            "email": request.form["email"],
            "password": request.form["password"]
        })

        session["access_token"] = res.session.access_token
        return redirect("/")

    return render_template("login.html")

# register page
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        supabase.auth.sign_up({
            "email": request.form["email"],
            "password": request.form["password"]
        })

        return redirect("/login")

    return render_template("register.html")

# logout function
@app.route("/logout")
def logout():
    token = session.get("access_token")
    if token:
        with _user_cache_lock:
            _user_cache.pop(token, None)
    session.clear()
    return redirect("/login")


# get user id, to use for postgres db queries
def get_current_user():
    if hasattr(g, "user"):
        return g.user

    token = session.get("access_token")
    if not token:
        g.user = None
        return None

    with _user_cache_lock:
        if token in _user_cache:
            g.user = _user_cache[token]
            return g.user

    try:
        supabase.auth.set_session(
            access_token=token,
            refresh_token=""
        )
        user_response = supabase.auth.get_user(token)
        g.user = getattr(user_response, "user", None)
        with _user_cache_lock:
            _user_cache[token] = g.user
    except Exception:
        g.user = None

    return g.user


# forgot password
@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    error = None
    if request.method == "POST":
        try:
            supabase.auth.reset_password_for_email(
                request.form["email"],
                options={
                    "redirect_to": os.getenv("APP_URL") + "/reset-password"
                }
            )
            return render_template("forgot_password.html",
                message="If this email exists, a reset link was sent.")
        
        except Exception as e:
            error = str(e)
        
    return render_template("forgot_password.html", error=error)

@app.route("/reset-password", methods=["GET", "POST"])
def reset_password():
    error = None
    if request.method == "POST":
        try:
            access_token = request.form["access_token"]
            new_password = request.form["password"]

            if not access_token or "." not in access_token:
                raise Exception("Invalid or expired reset link")

            supabase.auth.set_session(
                access_token=access_token,
                refresh_token=""
            )

            supabase.auth.update_user({"password": new_password})
            return redirect("/login")
    
        except Exception as e:
            error = str(e)

    return render_template("reset_password.html", error=error)


# main page
@app.route("/", methods=["GET", "POST"])
def index():
    user = get_current_user()
    if not user:
        return redirect("/login")

    user_id = user.id
    today = datetime.now(ZoneInfo("America/New_York")).date().isoformat()

    if request.method == "POST":
        checked_ids = {
            int(key.split("_")[1])
            for key in request.form
            if key.startswith("habit_")
        }

        habits = (
            supabase
            .table("habits")
            .select("id")
            .eq("user_id", user_id)
            .execute()
            .data
        )

        payload = [
            {
                "habit_id": h["id"],
                "log_date": today,
                "completed": h["id"] in checked_ids
            }
            for h in habits
        ]

        if payload:
            supabase.table("daily_habits").upsert(
                payload,
                on_conflict="habit_id,log_date"
            ).execute()

        invalidate_index_cache(user_id, today)
        return redirect("/")

    rows = get_index_habits(user_id, today)

    habit_names = {r["id"]: r["name"] for r in rows}
    today_status = {
        r["id"]: (r["daily_habits"][0]["completed"]
        if r["daily_habits"] else False)
        for r in rows
    }

    return render_template(
        "index.html",
        habit_names=habit_names,
        task_status=lambda hid: today_status.get(hid, False)
    )

# create new habit
@app.route("/api/create-habit", methods=["POST"])
def create_habit_api():
    user = get_current_user()
    if not user:
        return redirect("/login")

    user_id = user.id
    habit_name = request.form.get('name_input', '').strip()

    if not habit_name:
        flash("Habit name cannot be empty.", "error")
        return redirect("/")

    data = {
        "user_id": user_id,
        "name": habit_name
    }
    
    result = (
        supabase
        .table("habits")
        .upsert(data, on_conflict="user_id,name")
        .execute()
    )

    if result.data:
        flash("Habit created successfully!", "success")
    else:
        flash("Failed to create habit.", "error")

    today = datetime.now(ZoneInfo("America/New_York")).date().isoformat()
    invalidate_index_cache(user_id, today)
    return redirect("/")


@app.route("/api/delete-habit", methods=["POST"])
def delete_habit_api():
    user = get_current_user()
    if not user:
        return redirect("/login")

    habit_id_raw = request.form.get("habit_id")
    if not habit_id_raw:
        flash("Missing habit to delete.", "error")
        return redirect("/")

    try:
        habit_id = int(habit_id_raw)
    except (TypeError, ValueError):
        flash("Invalid habit.", "error")
        return redirect("/")

    user_id = user.id

    try:
        (
            supabase
            .table("habits")
            .delete()
            .eq("id", habit_id)
            .eq("user_id", user_id)
            .execute()
        )
        flash("Habit deleted successfully.", "success")
    except Exception:
        flash("Failed to delete habit.", "error")

    today = datetime.now(ZoneInfo("America/New_York")).date().isoformat()
    invalidate_index_cache(user_id, today)

    return redirect("/")


# history page with calendar
@app.route("/history")
def history():
    user = get_current_user()
    if not user:
        return redirect("/login")
    return render_template("history.html")

# request data
@app.route("/api/habit-data")
def habit_data_api():
    user = get_current_user()
    if not user:
        return redirect("/login")

    user_id = user.id

    habits = (
        supabase
        .table("habits")
        .select("id,name")
        .eq("user_id", user_id)
        .order("created_at")
        .execute()
        .data
    )

    habit_ids = [h["id"] for h in habits]
    if not habit_ids:
        return jsonify({"habits": [], "habitRows": []})

    habit_rows = (
        supabase
        .table("daily_habits")
        .select("habit_id,log_date,completed")
        .in_("habit_id", habit_ids)
        .order("log_date")
        .execute()
        .data
    )

    return jsonify({
        "habits": [[h["id"], h["name"]] for h in habits],
        "habitRows": [
            [r["habit_id"], r["log_date"], r["completed"]]
            for r in habit_rows
        ]
    })


if __name__ == "__main__":
    app.run()