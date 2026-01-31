from flask import Flask, render_template, request, redirect, jsonify, session, g
from supabase import create_client
import os
from dotenv import load_dotenv
from datetime import date

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

    g.user = supabase.auth.get_user(token).user
    return g.user


#forgot password
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
    today = date.today().isoformat()

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

        return redirect("/")

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
        return jsonify({"error": "Not authenticated"}), 401

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