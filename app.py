from flask import Flask, render_template, request, redirect, url_for, session
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import datetime
from functools import wraps
import os, json

app = Flask(__name__)
app.secret_key = "secret123"

# ---------------- Google Sheets Auth ----------------
scope = ["https://spreadsheets.google.com/feeds",
         "https://www.googleapis.com/auth/drive"]

# Load credentials from environment variable
creds_json = os.environ.get("GOOGLE_CREDS")  # Set this in Render or .env locally
if not creds_json:
    raise Exception("GOOGLE_CREDS environment variable not set!")

creds_dict = json.loads(creds_json)
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)
# -----------------------------------------------------

# Map department → branch → year → sheet_id
sheet_map = {
    "BTech": {
        "CSE": {"1": "1Yh6b4q4zD8KJex2924cwjU12SyVt60hFVKb0KmDnCvw", "2": "1Yh6b4q4zD8KJex2924cwjU12SyVt60hFVKb0KmDnCvw", "3": "SHEET_ID_3", "4": "SHEET_ID_4"},
        "AIML": {"1": "SHEET_ID_5", "2": "SHEET_ID_6"},
        "DS": {"1": "SHEET_ID_7"},
        "ECE": {"1": "SHEET_ID_8"},
        "EEE": {"1": "SHEET_ID_9"}
    },
    "Diploma": {
        "CSE": {"1": "SHEET_ID_10"}
    },
    "Pharmacy": {
        "Pharmaceutics": {"1": "SHEET_ID_11"}
    },
    "MBA": {
        "Finance": {"1": "SHEET_ID_12"},
        "HR": {"1": "SHEET_ID_13"}
    }
}

MASTER_FILE_ID = "11gy7F7TgcgDsfkT0Im9LUxo_T5ygSX6_6_cnC77gzmk" 

# ---------------- Login Required Decorator ----------------
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function

# ---------------- Routes ----------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if username == "svsgoi" and password == "svsgoi@tk":
            session["logged_in"] = True
            return redirect(url_for("home"))
        else:
            return render_template("login.html", error="Invalid username or password")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("logged_in", None)
    return redirect(url_for("login"))

@app.route("/")
@login_required
def home():
    return render_template("departments.html", departments=sheet_map.keys())

@app.route("/branch/<department>")
@login_required
def branch(department):
    return render_template("branches.html", department=department, branches=sheet_map[department].keys())

@app.route("/year/<department>/<branch>")
@login_required
def year(department, branch):
    return render_template("years.html", department=department, branch=branch, years=sheet_map[department][branch].keys())

@app.route("/sheet/<department>/<branch>/<year>")
@login_required
def sheet_view(department, branch, year):
    sheet_id = sheet_map[department][branch][year]
    sheet = client.open_by_key(sheet_id).sheet1
    data = sheet.get_all_values()
    headers = data[0]
    rows = data[1:]
    return render_template("sheet.html", department=department, branch=branch, year=year,
                           headers=headers, rows=rows)

@app.route("/submit_absent", methods=["POST"])
@login_required
def submit_absent():
    department = request.form.get("department")
    branch = request.form.get("branch")
    year = request.form.get("year")

    today = datetime.date.today().strftime("%Y-%m-%d")

    # Open master spreadsheet
    sh = client.open_by_key(MASTER_FILE_ID)
    worksheet = sh.sheet1  # Your svsAbsent sheet

    # Add headers if sheet is empty
    if not worksheet.get_all_values():
        worksheet.append_row(["Date", "Name", "Phone", "Department", "Branch", "Year", "HallTicket", "Attendance"])

    rows_to_add = []
    for key, value in request.form.items():
        if key.startswith("status_"):
            parts = value.split("|")
            if len(parts) == 4:
                status, name, phone, hallticket = parts
                attendance_status = "Present" if status == "present" else "Absent"
                rows_to_add.append([today, name, phone, department, branch, year, hallticket, attendance_status])

    for row in reversed(rows_to_add):
        worksheet.insert_row(row, 2)

    return "✅ Attendance saved successfully!"

if __name__ == "__main__":
    app.run(debug=True)
