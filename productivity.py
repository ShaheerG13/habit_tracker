from datetime import date
import json
from json.decoder import JSONDecodeError
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

class Task_Creator:
    def __init__(self, name, file):
        self.name = name
        self.file = "history_files/"+file
        try:
            with open(self.file, 'r') as f:
                self.history = json.load(f)
        except (FileNotFoundError, JSONDecodeError):
            self.history = {}

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

print(task1.file)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        for task in tasks:
            completed = task.name+"completed" in request.form
            print(request.form)
            task.daily_check(completed)

    return render_template("index.html", tasks=tasks)

@app.route("/history")
def history():
    print(task1.file)
    return render_template("history.html", tasks=tasks)


if __name__ == "__main__":
    app.run(debug=True)
