from flask import Flask, render_template, request, redirect, jsonify, g
import psycopg2
from psycopg2 import pool
from psycopg2.extras import execute_values
import os
from dotenv import load_dotenv
from datetime import date

app = Flask(__name__)
load_dotenv()

db_pool = psycopg2.pool.SimpleConnectionPool(1, 5, os.getenv("DB_URL"))

def get_db():
    if "db" not in g:
        g.db = db_pool.getconn()
        g.curr = g.db.cursor()
    return g.db, g.curr

@app.teardown_appcontext
def close_db(exception):
    db = g.pop("db", None)
    curr = g.pop("curr", None)
    if curr is not None:
        curr.close()
    if db is not None:
        db_pool.putconn(db)


def get_user(username, curr):
    curr.execute("SELECT id FROM users WHERE username = %s", (username,))
    row = curr.fetchone()
    return row[0] if row else None


def get_habit_data(user_id, curr):
    curr.execute("""
        SELECT id, name
        FROM habits
        WHERE user_id = %s
        ORDER BY created_at
    """, (user_id,))
    habits = curr.fetchall()

    curr.execute("""
        SELECT habit_id, log_date, completed
        FROM daily_habits
        WHERE habit_id IN (
            SELECT id FROM habits WHERE user_id = %s
        )
        ORDER BY log_date
    """, (user_id,))
    habit_rows = curr.fetchall()

    return habits, habit_rows

"""
class Task_Creator:
    def __init__(self, name):
        self.name = name

    def daily_check(self, completed: bool):
        today = date.today().isoformat()
        self.history[today] = completed

        with open(self.file, 'w') as f:
            json.dump(self.history, f, indent=2)
    
    def today(self):
        today = date.today().isoformat()
        return self.history.get(today)

task1 = Task_Creator("Reading", "reading_history.json")
task2 = Task_Creator("Water", "water_history.json")
task3 = Task_Creator("Sleep", "sleep_history.json")
tasks = [task1, task2, task3]
"""


# flask stuff
@app.route("/", methods=["GET", "POST"])
def index():
    db, curr = get_db()
    user_id = get_user("default", curr)
    today = date.today()

    if request.method == 'POST':
        checked = {
            int(key.split("_")[1])
            for key in request.form
            if key.startswith("habit_")
        }

        curr.execute(
            "SELECT id FROM habits WHERE user_id = %s",
            (user_id,)
        )
        habit_ids = [row[0] for row in curr.fetchall()]

        data = [(hid, today, hid in checked) for hid in habit_ids]

        if data:
            query = """
                INSERT INTO daily_habits (habit_id, log_date, completed)
                VALUES %s
                ON CONFLICT (habit_id, log_date)
                DO UPDATE SET completed = EXCLUDED.completed
            """
            execute_values(curr, query, data)
            db.commit()

        return redirect("/")


    # Get request
    curr.execute("""
        SELECT h.id, h.name, COALESCE(d.completed, FALSE)
        FROM habits h
        LEFT JOIN daily_habits d
        ON h.id = d.habit_id
        AND d.log_date = %s
        WHERE h.user_id = %s
        ORDER BY h.created_at
    """, (today, user_id,))

    rows = curr.fetchall()

    habit_names = {hid: name for hid, name, _ in rows}
    today_status = {hid: completed for hid, _, completed in rows}

    return render_template(
        "index.html",
        habit_names=habit_names,
        task_status=lambda hid: today_status.get(hid, False)
    )


@app.route("/history")
def history():
    return render_template("history.html")


@app.route("/api/habit-data")
def habit_data_api():
    """ TESTING
    return jsonify({
        'habits': [[1, 'Morning Exercise'], [2, 'Read 30 Minutes']],
        'habitRows': [
            [1, '2026-01-01', True],
            [1, '2026-01-02', False],
            [2, '2026-01-01', True]
        ]
    })
"""
    db, curr = get_db()

    user_id = get_user("default", curr)
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401
    
    habits, habit_rows = get_habit_data(user_id, curr)

    return jsonify({
        'habits': [[int(hid), name] for hid, name in habits],
        'habitRows': [
            [int(habit_id), day.isoformat(), bool(completed)] 
            for habit_id, day, completed in habit_rows
        ]
    })


if __name__ == "__main__":
    app.run(debug=True)
