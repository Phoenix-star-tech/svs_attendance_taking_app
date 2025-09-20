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

creds_dict = {
    "type": "service_account",
    "project_id": "ultra-ridge-472307-j6",
    "private_key_id": "d309bc3a5aa75e467bcc6f303159578ca31cf72d",
    "private_key": "-----BEGIN PRIVATE KEY-----\\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQC3FBX9ZYb5sMfz\\nEJznKlGAluC69IxskPh7lzwb+OQ1sGNkyqiEuV5pI0JPf8x3O3GClQ/93FPr4uMB\\nm3PpopepQ7ydj/uBWDE1rk4i1txcWqX0NEgzKb77r5T9S3nDgas7I/nP7aB3hWZ3\\nrCHSOIEK1AEOx/rdYA8nvGL5bXyNJNgVdonKInwS85hJvE36rkBfJ/4RVAEVZz48\\niDDMjvSIX4T6IhXKlK0bW2gdUJUagtrsGVJBdYTq6vxAkxxNka7tl/4oJY4OsY61\\nmLLNFdneJa/UogHo1kP2i6RbHNoy7MM8TfFuY+8iIUhuHGAcYeaONNLPBf495BAL\\nHw4PEonZAgMBAAECggEATEGEBUdgKKmPJzmQuSKhzwdJNOX+hYv+y+/K3DXXzFsb\\nk1RsS9gwMGe8y4NGRZWPap4vCoTWucaH2lgHOFX+iMTLj+90iUQUPzFKn21SXO9u\\n92A9gH4PbCMO0lA5OAtPKLOL7qUiNRZt/0PF1JuveDSk+iSm48WKmnj32r/VZK4x\\nHzvR4m5yIDqOimjHce/2GEanMrxd1DM6r9ZWWkr/2LoiEW7PTlGK4hvDeVcaoJ+l\\n1Xg5roGkO4N5tjOGeB7OoaDibD0WlLXtXriIUmIj0hiK1tWfqIMjdxZVeY28WXxt\\n2LP443k/z/1LOSR2DOfTd5REaEImf7VdBG7oeUJdVwKBgQD70y/5CKi/v80MFg7p\\nqiNZLTbPZQiTS8ppSFFwgZ50JYqoMMgzro81KDjrKlyt02/ysC2ke7+XdvAwPqz+\\nBBCQJZUb/pP36semuyJD6pLBzcaDytZLkRiQIgA94bnMB35ipWfVJRXkJ3uygMMe\\nL3x2awwbTeyJMWQFG9k5Uur30wKBgQC6HR62P0tbAF4x8ABomTD4lt4PfeGvWEla\\nc4bVhNnVTZXiqn+GXweXP3ZLjaicfBmagvWkQ+//3spG5aK4fGgIBWjsAh6R46GP\\n975u+FJCk9wAHx4IonydFz+daZP9zrFWvu+WFLOXa1fQu8FaaIUokaLZO4lXPxPr\\ngEJ4RQG4IwKBgE7e8BGBYsjbm68DYZxRi0ys2pPOQwdPH5Al9EvWbPhXobvXu3xk\\nWbn+ZQVSeUCADnnmMAVqNLGNsOCLYMcWItHi03a3H0TwpaNUzQCUgW5tspUofEGi\\nqhzKaWT4Q6bhWfYvc/vP57FTpGxd476ahNLZ6CrNFx5I99iZxkkr7Se9AoGAZavm\\nzTTCm9IVoz4zWvDlGciBQwFHuxyF5g3aiOZsgeRCj3MI+4UKhou6ugeHJwV8jzYf\\nrz8V6zfwVM66GAKOamNaMCPwQ06RQi7bL5AkkA5qTv6wz5LEdKTwsbOtjyfNJVBl\\nXh2tBnkzneoT9KnIpKL6zaWCn9Drtul4Zm98QvUCgYEAxG0LiRyJY179dhxGj4CW\\noXRmUqaNViUGA93D+bgkefCF+zrW54qNhJDMj+o3+szLFz2oYkDbjPsQYH/18M3G\\ncozYCuuVOeX0iyZ6d+ILJWCE+LmINMmAngBXDT7QtOmATm24JVzcJhub9h2U2gMz\\nb0OYlvApi5xZKPbhOWAsE5I=\\n-----END PRIVATE KEY-----\\n",
    "client_email": "attendance-service@ultra-ridge-472307-j6.iam.gserviceaccount.com",
    "client_id": "117548735903945328880",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/attendance-service%40ultra-ridge-472307-j6.iam.gserviceaccount.com",
    "universe_domain": "googleapis.com"
}

# Load credentials from environment variable
creds_json = os.environ.get("GOOGLE_CREDS")  # Set this in Render or .env locally
if not creds_json:
    raise Exception("GOOGLE_CREDS environment variable not set!")

creds_dict = json.loads(creds_json)
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)

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

