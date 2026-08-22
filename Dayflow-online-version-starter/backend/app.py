
import os
import secrets
import sqlite3
from datetime import datetime, date
from functools import wraps

from flask import Flask, jsonify, request, session, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.path.join(BASE, "dayflow.db")
FRONTEND = os.path.join(BASE, "frontend")

app = Flask(__name__)
app.secret_key = os.getenv("DAYFLOW_SECRET", "dev-secret-change-this")

def connect():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA foreign_keys=ON")
    return c

def rows(sql, params=()):
    c = connect()
    try:
        return [dict(x) for x in c.execute(sql, params).fetchall()]
    finally:
        c.close()

def row(sql, params=()):
    r = rows(sql, params)
    return r[0] if r else None

def execute(sql, params=()):
    c = connect()
    try:
        cur = c.execute(sql, params)
        c.commit()
        return cur.lastrowid
    finally:
        c.close()

def now():
    return datetime.now().isoformat(timespec="seconds")

def current_user():
    eid = session.get("employee_id")
    if not eid:
        return None
    return row("""
        SELECT e.*, d.department_name
        FROM employees e
        LEFT JOIN departments d ON d.department_id=e.department_id
        WHERE e.employee_id=?
    """, (eid,))

def auth_required(fn):
    @wraps(fn)
    def wrapper(*a, **kw):
        if not current_user():
            return jsonify(error="Authentication required"), 401
        return fn(*a, **kw)
    return wrapper

def admin_required(fn):
    @wraps(fn)
    def wrapper(*a, **kw):
        u = current_user()
        if not u:
            return jsonify(error="Authentication required"), 401
        if u["role"] != "ADMIN":
            return jsonify(error="Admin access required"), 403
        return fn(*a, **kw)
    return wrapper

def generate_code(first, last, joining):
    year = datetime.strptime(joining, "%Y-%m-%d").year
    count = row("SELECT COUNT(*) n FROM employees WHERE substr(joining_date,1,4)=?", (str(year),))["n"]
    return f"OI{first[:2]}{last[:2]}{year}{count+1:03d}"

def get_department(name):
    name = name or "General"
    d = row("SELECT department_id FROM departments WHERE department_name=?", (name,))
    if d:
        return d["department_id"]
    return execute("INSERT INTO departments(department_name) VALUES(?)", (name,))

def office():
    settings = row("SELECT * FROM office_settings WHERE id=1")
    if not settings:
        execute(
            "INSERT INTO office_settings(id,office_name,current_code,code_generated_at,rotation_seconds) VALUES(1,?,?,?,45)",
            ("Bengaluru Main Office", "DF-4821", now())
        )
        settings = row("SELECT * FROM office_settings WHERE id=1")
    try:
        age = (datetime.now() - datetime.fromisoformat(settings["code_generated_at"])).total_seconds()
    except Exception:
        age = 0
    remain = int(settings["rotation_seconds"] - age)
    if remain <= 0:
        return rotate_office()
    return {**settings, "remaining_seconds": remain}

def rotate_office():
    code = f"DF-{secrets.randbelow(9000)+1000}"
    execute(
        "UPDATE office_settings SET current_code=?,code_generated_at=? WHERE id=1",
        (code, now())
    )
    settings = row("SELECT * FROM office_settings WHERE id=1")
    return {**settings, "remaining_seconds": settings["rotation_seconds"]}

def seed():
    if row("SELECT employee_id FROM employees LIMIT 1"):
        return

    for d in ["Engineering", "Design", "Finance", "People Ops", "Marketing", "Sales"]:
        execute("INSERT INTO departments(department_name) VALUES(?)", (d,))
    for name, desc in [
        ("Paid", "Paid annual leave"),
        ("Sick", "Medical leave"),
        ("Unpaid", "Unpaid personal leave")
    ]:
        execute("INSERT INTO leave_types(leave_name,description) VALUES(?,?)", (name, desc))

    demo = [
        ("OIAnSh2025001","Ananya","Sharma","ananya@dayflow.demo","+91 90000 10001","Bengaluru","Engineering","Software Engineer","2025-06-17","EMPLOYEE","Dayflow@123"),
        ("OIRaMe2024002","Rahul","Menon","rahul@dayflow.demo","+91 90000 10002","Bengaluru","Design","Product Designer","2024-08-05","EMPLOYEE","Dayflow@123"),
        ("OIPrNa2023003","Priya","Nair","priya@dayflow.demo","+91 90000 10003","Bengaluru","Finance","Finance Analyst","2023-01-09","EMPLOYEE","Dayflow@123"),
        ("OIAdMi2020001","Admin","Manager","admin@dayflow.demo","+91 90000 19999","Bengaluru","People Ops","HR Administrator","2020-01-01","ADMIN","Admin@123")
    ]

    for code, first, last, email, phone, loc, dept, title, joining, role, password in demo:
        dep_id = get_department(dept)
        eid = execute("""INSERT INTO employees(
            employee_code,first_name,last_name,email,phone,location,department_id,job_title,joining_date,role
        ) VALUES(?,?,?,?,?,?,?,?,?,?)""",
            (code, first, last, email, phone, loc, dep_id, title, joining, role)
        )
        execute("""INSERT INTO user_accounts(employee_id,password_hash,must_change_password)
                   VALUES(?,?,0)""", (eid, generate_password_hash(password)))

    # Salary records for the three employee demos.
    data = {
        "OIAnSh2025001": [("Basic salary","EARNING",35100),("HRA","EARNING",15600),("Special allowance","EARNING",15600),("Other benefits","EARNING",11700),("Performance bonus","EARNING",5000),("Overtime","EARNING",2500),("PF","DEDUCTION",2000),("Professional tax","DEDUCTION",200),("Other deduction","DEDUCTION",500)],
        "OIRaMe2024002": [("Basic salary","EARNING",31050),("HRA","EARNING",13800),("Special allowance","EARNING",13800),("Other benefits","EARNING",10350),("Performance bonus","EARNING",3000),("PF","DEDUCTION",1800),("Professional tax","DEDUCTION",200)],
        "OIPrNa2023003": [("Basic salary","EARNING",27900),("HRA","EARNING",12400),("Special allowance","EARNING",12400),("Other benefits","EARNING",9300),("PF","DEDUCTION",1600),("Professional tax","DEDUCTION",200)]
    }
    for code, comps in data.items():
        eid = row("SELECT employee_id FROM employees WHERE employee_code=?", (code,))["employee_id"]
        rev = execute("""INSERT INTO salary_revisions(employee_id,effective_date,reason,note,status,created_by)
                         VALUES(?,?,?,?,?,?)""", (eid, "2026-01-01", "Starting salary", "", "PROCESSED", 4))
        for name, typ, amount in comps:
            execute("""INSERT INTO salary_components(revision_id,component_name,component_type,amount)
                       VALUES(?,?,?,?)""", (rev, name, typ, amount))

    # Attendance demo.
    for code, d, cin, cout, st in [
        ("OIAnSh2025001","2026-08-21","09:04","18:06","PRESENT"),
        ("OIAnSh2025001","2026-08-20","09:16","17:52","PRESENT"),
        ("OIAnSh2025001","2026-08-19","09:02","13:12","HALF_DAY"),
        ("OIRaMe2024002","2026-08-21","09:12","18:01","PRESENT"),
        ("OIPrNa2023003","2026-08-21","10:01","18:04","PRESENT")
    ]:
        eid = row("SELECT employee_id FROM employees WHERE employee_code=?", (code,))["employee_id"]
        execute("""INSERT INTO attendance(
            employee_id,attendance_date,check_in,check_out,status,verification_method,office_verified
        ) VALUES(?,?,?,?,?,'OFFICE_CODE',1)""", (eid, d, cin, cout, st))

    # Leave demo.
    for code, typ, start, end, reason, status_value, comment in [
        ("OIAnSh2025001","Paid","2026-09-03","2026-09-04","Family function","PENDING",""),
        ("OIRaMe2024002","Sick","2026-08-27","2026-08-27","Medical appointment","APPROVED","Approved by HR"),
        ("OIPrNa2023003","Unpaid","2026-09-10","2026-09-12","Personal work","REJECTED","Please discuss dates")
    ]:
        eid = row("SELECT employee_id FROM employees WHERE employee_code=?", (code,))["employee_id"]
        ltid = row("SELECT leave_type_id FROM leave_types WHERE leave_name=?", (typ,))["leave_type_id"]
        execute("""INSERT INTO leave_requests(
            employee_id,leave_type_id,start_date,end_date,reason,status,reviewed_by,reviewed_at,reviewer_comment
        ) VALUES(?,?,?,?,?,?,?,?,?)""",
            (eid, ltid, start, end, reason, status_value, 4, now() if status_value != "PENDING" else None, comment or None))

    for title, desc, event_date in [
        ("Team review", "Weekly team review", "2026-08-25"),
        ("Payroll close", "Monthly payroll processing", "2026-08-28"),
        ("Office town hall", "People & operations meeting", "2026-09-03")
    ]:
        execute("""INSERT INTO company_events(title,description,event_date,created_by)
                   VALUES(?,?,?,?)""", (title, desc, event_date, 4))

    execute("""INSERT OR REPLACE INTO office_settings(
        id,office_name,current_code,code_generated_at,rotation_seconds
    ) VALUES(1,'Bengaluru Main Office','DF-4821',?,45)""", (now(),))

@app.before_request
def startup():
    if not getattr(app, "_ready", False):
        with open(os.path.join(BASE, "database", "schema.sql"), encoding="utf-8") as f:
            connect().executescript(f.read())
        seed()
        app._ready = True

@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def frontend(path):
    file_path = os.path.join(FRONTEND, path)
    if path and os.path.isfile(file_path):
        return send_from_directory(FRONTEND, path)
    return send_from_directory(FRONTEND, "index.html")

@app.post("/api/auth/login")
def login():
    d = request.get_json(silent=True) or {}
    login_value = (d.get("login") or "").strip().lower()
    password = d.get("password") or ""
    role = (d.get("role") or "").upper()

    u = row("""SELECT e.*,d.department_name,a.password_hash
               FROM employees e
               LEFT JOIN departments d ON d.department_id=e.department_id
               JOIN user_accounts a ON a.employee_id=e.employee_id
               WHERE lower(e.employee_code)=lower(?) OR lower(e.email)=lower(?)
               LIMIT 1""", (login_value, login_value))
    if not u or not check_password_hash(u["password_hash"], password):
        return jsonify(error="The ID/email or password does not match."), 401
    if u["role"] != role:
        return jsonify(error="That account belongs to the other role."), 403

    session["employee_id"] = u["employee_id"]
    execute("UPDATE user_accounts SET last_login=? WHERE employee_id=?", (now(), u["employee_id"]))

    u.pop("password_hash", None)
    return jsonify(user=u)

@app.post("/api/auth/register")
def register():
    d = request.get_json(silent=True) or {}
    first, last = (d.get("first_name") or "").strip(), (d.get("last_name") or "").strip()
    email, joining = (d.get("email") or "").strip(), d.get("joining_date") or ""
    role = (d.get("role") or "EMPLOYEE").upper()

    if not first or not last or not email or not joining:
        return jsonify(error="Name, email and joining date are required"), 400
    if role == "ADMIN" and d.get("admin_code") != os.getenv("DAYFLOW_ADMIN_CODE", "DAYFLOW-ADMIN"):
        return jsonify(error="Invalid HR invite code"), 403
    if row("SELECT employee_id FROM employees WHERE lower(email)=lower(?)", (email,)):
        return jsonify(error="Email already exists"), 409

    code = generate_code(first, last, joining)
    temp = f"Df!{secrets.token_urlsafe(5)}9"
    dep_id = get_department(d.get("department"))
    eid = execute("""INSERT INTO employees(
      employee_code,first_name,last_name,email,department_id,job_title,joining_date,role
    ) VALUES(?,?,?,?,?,?,?,?)""",
        (code,first,last,email,dep_id,d.get("job_title") or "Employee",joining,role))
    execute("""INSERT INTO user_accounts(employee_id,password_hash,must_change_password)
               VALUES(?,?,1)""", (eid, generate_password_hash(temp)))

    rev = execute("""INSERT INTO salary_revisions(
      employee_id,effective_date,reason,status,created_by
    ) VALUES(?,?,?,?,?)""",
        (eid, joining, "Starting salary", "PROCESSED", session.get("employee_id")))
    for name, amount in [("Basic salary",22500),("HRA",10000),("Special allowance",10000),("Other benefits",7500)]:
        execute("""INSERT INTO salary_components(revision_id,component_name,component_type,amount)
                   VALUES(?,?,?,?)""", (rev,name,"EARNING",amount))

    return jsonify(employee_code=code, temporary_password=temp), 201

@app.post("/api/auth/logout")
def logout():
    session.clear()
    return jsonify(ok=True)

@app.get("/api/auth/me")
def auth_me():
    u = current_user()
    if not u:
        return jsonify(error="Not signed in"), 401
    return jsonify(user=u)

@app.get("/api/dashboard")
@auth_required
def dashboard():
    u = current_user()
    o = office()

    if u["role"] == "ADMIN":
        staff = row("SELECT COUNT(*) n FROM employees WHERE role='EMPLOYEE' AND employment_status='ACTIVE'")["n"]
        present = row("SELECT COUNT(*) n FROM attendance WHERE attendance_date=? AND status='PRESENT'",
                      (date.today().isoformat(),))["n"]
        pending = row("SELECT COUNT(*) n FROM leave_requests WHERE status='PENDING'")["n"]

        payroll_rows = rows("""SELECT sr.revision_id,e.employee_id,e.first_name,e.last_name,
                                      sc.component_type,sc.amount
                               FROM salary_revisions sr
                               JOIN employees e ON e.employee_id=sr.employee_id
                               JOIN salary_components sc ON sc.revision_id=sr.revision_id
                               WHERE e.role='EMPLOYEE'
                               AND sr.status IN ('DRAFT','PROCESSED')
                               AND sr.revision_id IN (
                                  SELECT MAX(revision_id) FROM salary_revisions
                                  GROUP BY employee_id
                               )""")
        wages = sum(float(x["amount"]) for x in payroll_rows if x["component_type"] == "EARNING")

        pending_requests = rows("""SELECT lr.leave_request_id,
                    e.first_name || ' ' || e.last_name employee_name,
                    lt.leave_name,lr.start_date,lr.end_date,lr.status
                FROM leave_requests lr
                JOIN employees e ON e.employee_id=lr.employee_id
                JOIN leave_types lt ON lt.leave_type_id=lr.leave_type_id
                WHERE lr.status='PENDING'
                ORDER BY lr.created_at DESC LIMIT 6""")

        return jsonify(
            staff_count=staff,
            present_today=present,
            pending_leave=pending,
            monthly_wages=wages,
            office_code=o["current_code"],
            office_remaining_seconds=o["remaining_seconds"],
            pending_requests=pending_requests,
            weekly_attendance=[62,78,71,89,84,92,88]
        )

    present_days = row("""SELECT COUNT(*) n FROM attendance
                          WHERE employee_id=? AND status='PRESENT'
                          AND substr(attendance_date,1,7)=substr(date('now'),1,7)""",
                       (u["employee_id"],))["n"]

    leave_remaining = row("""SELECT COALESCE(SUM(allocated_days-used_days),0) n
                             FROM leave_balances
                             WHERE employee_id=? AND leave_year=strftime('%Y','now')""",
                          (u["employee_id"],))["n"]

    sal = current_salary(u["employee_id"])
    recent = rows("""SELECT attendance_date,check_in,check_out,status,verification_method
                     FROM attendance
                     WHERE employee_id=?
                     ORDER BY attendance_date DESC LIMIT 8""",(u["employee_id"],))

    return jsonify(
        present_days=present_days,
        leave_remaining=leave_remaining,
        monthly_wage=sal["gross_salary"] if sal else 0,
        department_name=u["department_name"],
        recent_attendance=recent
    )

def current_revision(employee_id):
    return row("""SELECT * FROM salary_revisions
                  WHERE employee_id=?
                  ORDER BY effective_date DESC, revision_id DESC LIMIT 1""",(employee_id,))

def current_salary(employee_id):
    rev = current_revision(employee_id)
    if not rev:
        return None
    comps = rows("SELECT * FROM salary_components WHERE revision_id=?", (rev["revision_id"],))
    gross = sum(float(c["amount"]) for c in comps if c["component_type"]=="EARNING")
    deductions = sum(float(c["amount"]) for c in comps if c["component_type"]=="DEDUCTION")
    basic = sum(float(c["amount"]) for c in comps if c["component_type"]=="EARNING" and c["component_name"]=="Basic salary")
    allowances = sum(float(c["amount"]) for c in comps if c["component_type"]=="EARNING" and c["component_name"] not in ("Basic salary","Performance bonus","Overtime"))
    bonus_ot = sum(float(c["amount"]) for c in comps if c["component_name"] in ("Performance bonus","Overtime"))
    return {
        "revision_id":rev["revision_id"],"effective_date":rev["effective_date"],
        "gross_salary":gross,"deductions":deductions,"net_salary":gross-deductions,
        "basic_salary":basic,"allowances":allowances,"bonus_overtime":bonus_ot
    }

@app.get("/api/employees")
@auth_required
def list_employees():
    return jsonify(employees=rows("""SELECT e.employee_id,e.employee_code,e.first_name,e.last_name,e.email,
               e.phone,e.location,e.job_title,e.joining_date,e.role,e.employment_status,d.department_name
        FROM employees e LEFT JOIN departments d ON d.department_id=e.department_id
        WHERE e.role='EMPLOYEE' ORDER BY e.first_name,e.last_name"""))

@app.get("/api/employees/me")
@auth_required
def my_profile():
    return jsonify(employee=current_user())

@app.get("/api/employees/<int:eid>")
@auth_required
def profile_card(eid):
    viewer=current_user()
    if viewer["role"] != "ADMIN" and viewer["employee_id"] != eid:
        return jsonify(error="You may only view your own profile"),403
    u=row("""SELECT e.*,d.department_name
             FROM employees e LEFT JOIN departments d ON d.department_id=e.department_id
             WHERE e.employee_id=?""",(eid,))
    if not u:return jsonify(error="Employee not found"),404
    s=current_salary(eid)
    u["salary"] = s["gross_salary"] if s else 0
    return jsonify(employee=u)

@app.patch("/api/employees/me")
@auth_required
def update_profile():
    d=request.get_json(silent=True) or {}
    eid=current_user()["employee_id"]
    execute("UPDATE employees SET phone=?,location=?,updated_at=? WHERE employee_id=?",
            (d.get("phone"),d.get("location"),now(),eid))
    return jsonify(employee=current_user())

@app.post("/api/employees")
@admin_required
def admin_create_employee():
    d=request.get_json(silent=True) or {}
    first=(d.get("first_name") or "").strip()
    last=(d.get("last_name") or "").strip()
    email=(d.get("email") or "").strip()
    joining=d.get("joining_date") or ""
    if not first or not last or not email or not joining:
        return jsonify(error="Complete the employee details."),400
    if row("SELECT employee_id FROM employees WHERE lower(email)=lower(?)",(email,)):
        return jsonify(error="Email already exists"),409
    code=generate_code(first,last,joining)
    temp=f"Df!{secrets.token_urlsafe(5)}9"
    dep_id=get_department(d.get("department"))
    eid=execute("""INSERT INTO employees(
      employee_code,first_name,last_name,email,department_id,job_title,joining_date,role
    ) VALUES(?,?,?,?,?,?,?,'EMPLOYEE')""",
      (code,first,last,email,dep_id,d.get("job_title") or "Employee",joining))
    execute("INSERT INTO user_accounts(employee_id,password_hash,must_change_password) VALUES(?,?,1)",
            (eid,generate_password_hash(temp)))
    rev=execute("""INSERT INTO salary_revisions(employee_id,effective_date,reason,status,created_by)
                   VALUES(?,?,?,?,?)""",(eid,joining,"Starting salary","PROCESSED",current_user()["employee_id"]))
    for name,amount in [("Basic salary",22500),("HRA",10000),("Special allowance",10000),("Other benefits",7500)]:
        execute("INSERT INTO salary_components(revision_id,component_name,component_type,amount) VALUES(?,?,?,?)",
                (rev,name,"EARNING",amount))
    return jsonify(employee={"employee_id":eid},employee_code=code,temporary_password=temp),201

@app.get("/api/attendance/office-code")
@auth_required
def attendance_code():
    o=office()
    return jsonify(code=o["current_code"],remaining_seconds=o["remaining_seconds"],office_name=o["office_name"])

@app.post("/api/attendance/office-code/rotate")
@admin_required
def rotate_code():
    o=rotate_office()
    return jsonify(code=o["current_code"],remaining_seconds=o["remaining_seconds"])

@app.post("/api/attendance/check-in")
@auth_required
def checkin():
    u=current_user()
    if u["role"]!="EMPLOYEE":
        return jsonify(error="Only employees can check in here"),403
    d=request.get_json(silent=True) or {}
    o=office()
    if str(d.get("office_code","")).strip().upper()!=o["current_code"]:
        return jsonify(error="That office code is invalid or expired."),400
    today=date.today().isoformat()
    if row("SELECT attendance_id FROM attendance WHERE employee_id=? AND attendance_date=?",(u["employee_id"],today)):
        return jsonify(error="Attendance is already marked today."),409
    execute("""INSERT INTO attendance(
        employee_id,attendance_date,check_in,status,verification_method,office_verified,location_verified
    ) VALUES(?,?,?,'PRESENT','OFFICE_CODE',1,?)""",
        (u["employee_id"],today,datetime.now().strftime("%H:%M"),int(bool(d.get("location_verified")))))
    return jsonify(ok=True)

@app.get("/api/attendance")
@auth_required
def attendance_list():
    u=current_user()
    if u["role"]=="ADMIN":
        rec=rows("""SELECT a.*,e.first_name || ' ' || e.last_name employee_name
                    FROM attendance a JOIN employees e ON e.employee_id=a.employee_id
                    ORDER BY a.attendance_date DESC,a.check_in DESC""")
    else:
        rec=rows("""SELECT a.*,e.first_name || ' ' || e.last_name employee_name
                    FROM attendance a JOIN employees e ON e.employee_id=a.employee_id
                    WHERE a.employee_id=?
                    ORDER BY a.attendance_date DESC,a.check_in DESC""",(u["employee_id"],))
    o=office()
    return jsonify(
        records=rec,
        present_count=sum(1 for x in rec if x["status"]=="PRESENT"),
        half_day_count=sum(1 for x in rec if x["status"]=="HALF_DAY"),
        office_code=o["current_code"],
        office_remaining_seconds=o["remaining_seconds"]
    )

@app.get("/api/leave-types")
@auth_required
def leave_types():
    return jsonify(types=rows("SELECT leave_type_id,leave_name FROM leave_types ORDER BY leave_type_id"))

@app.get("/api/leaves")
@auth_required
def leaves():
    u=current_user()
    if u["role"]=="ADMIN":
        return jsonify(pending=rows("""SELECT lr.leave_request_id,
                    e.first_name || ' ' || e.last_name employee_name,
                    lt.leave_name,lr.start_date,lr.end_date,lr.reason,lr.status
                    FROM leave_requests lr
                    JOIN employees e ON e.employee_id=lr.employee_id
                    JOIN leave_types lt ON lt.leave_type_id=lr.leave_type_id
                    WHERE lr.status='PENDING' ORDER BY lr.created_at"""))
    return jsonify(requests=rows("""SELECT lr.leave_request_id,lt.leave_name,
                    lr.start_date,lr.end_date,lr.reason,lr.status,lr.reviewer_comment
                    FROM leave_requests lr JOIN leave_types lt ON lt.leave_type_id=lr.leave_type_id
                    WHERE lr.employee_id=? ORDER BY lr.created_at DESC""",(u["employee_id"],)))

@app.post("/api/leaves")
@auth_required
def create_leave():
    u=current_user()
    d=request.get_json(silent=True) or {}
    if not d.get("start_date") or not d.get("end_date") or not d.get("leave_type_id"):
        return jsonify(error="Leave type and dates are required"),400
    if d["end_date"] < d["start_date"]:
        return jsonify(error="End date cannot be before start date"),400
    execute("""INSERT INTO leave_requests(
        employee_id,leave_type_id,start_date,end_date,reason,status
    ) VALUES(?,?,?,?,?,'PENDING')""",
        (u["employee_id"],int(d["leave_type_id"]),d["start_date"],d["end_date"],d.get("reason","")))
    return jsonify(ok=True),201

@app.patch("/api/leaves/<int:lid>/decision")
@admin_required
def decision(lid):
    d=request.get_json(silent=True) or {}
    decision=(d.get("decision") or "").upper()
    if decision not in ("APPROVED","REJECTED"):
        return jsonify(error="Invalid decision"),400
    execute("""UPDATE leave_requests SET status=?,reviewed_by=?,reviewed_at=?,reviewer_comment=?
               WHERE leave_request_id=? AND status='PENDING'""",
            (decision,current_user()["employee_id"],now(),d.get("comment",""),lid))
    return jsonify(ok=True)

@app.get("/api/payroll")
@admin_required
def payroll():
    employees=rows("SELECT employee_id,first_name,last_name,employee_code FROM employees WHERE role='EMPLOYEE' ORDER BY first_name")
    result=[]
    total_gross=0;total_net=0
    for e in employees:
        s=current_salary(e["employee_id"]) or {"gross_salary":0,"net_salary":0,"deductions":0,"basic_salary":0,"allowances":0,"bonus_overtime":0}
        result.append({
            "employee_id":e["employee_id"],
            "employee_name":e["first_name"]+" "+e["last_name"],
            "employee_code":e["employee_code"],
            "department_name":row("SELECT d.department_name FROM employees e LEFT JOIN departments d ON d.department_id=e.department_id WHERE e.employee_id=?",(e["employee_id"],))["department_name"],
            **s
        })
        total_gross += s["gross_salary"]; total_net += s["net_salary"]
    revisions=rows("""SELECT sr.effective_date,sr.reason,sr.status,sr.gross_salary,
                             e.first_name || ' ' || e.last_name employee_name
                      FROM salary_revisions sr
                      JOIN employees e ON e.employee_id=sr.employee_id
                      ORDER BY sr.created_at DESC LIMIT 10""")
    for r in revisions:
        # gross_salary isn't a stored column; calculate it from the revision components.
        comps=rows("SELECT amount,component_type FROM salary_components WHERE revision_id=?",(row(
            "SELECT revision_id FROM salary_revisions WHERE employee_id=? AND effective_date=? AND reason=? ORDER BY revision_id DESC LIMIT 1",
            (row("SELECT employee_id FROM employees WHERE first_name || ' ' || last_name=?",(r["employee_name"],))["employee_id"],r["effective_date"],r["reason"])
        )["revision_id"],))
        r["gross_salary"]=sum(float(c["amount"]) for c in comps if c["component_type"]=="EARNING")
    return jsonify(records=result,total_gross=total_gross,total_net=total_net,revisions=revisions,
                   revision_count=row("SELECT COUNT(*) n FROM salary_revisions")["n"])

@app.get("/api/payroll/me")
@auth_required
def payroll_me():
    u=current_user()
    s=current_salary(u["employee_id"])
    rev=current_revision(u["employee_id"])
    comps=[]
    if rev:
        comps=rows("SELECT component_name name,component_type type,amount FROM salary_components WHERE revision_id=? ORDER BY component_id",(rev["revision_id"],))
    return jsonify(record=s,components=comps)

@app.get("/api/payroll/<int:eid>")
@admin_required
def payroll_one(eid):
    u=row("""SELECT e.*,d.department_name
             FROM employees e LEFT JOIN departments d ON d.department_id=e.department_id
             WHERE e.employee_id=?""",(eid,))
    if not u:return jsonify(error="Employee not found"),404
    s=current_salary(eid) or {"gross_salary":0,"deductions":0,"net_salary":0}
    rev=current_revision(eid)
    comps=rows("SELECT component_name name,component_type type,amount FROM salary_components WHERE revision_id=?",(rev["revision_id"],)) if rev else []
    return jsonify(employee=u,gross_salary=s["gross_salary"],deductions=s["deductions"],net_salary=s["net_salary"],components=comps)

@app.put("/api/payroll/<int:eid>")
@admin_required
def payroll_update(eid):
    d=request.get_json(silent=True) or {}
    components=d.get("components") or []
    if not components:return jsonify(error="At least one component is required"),400
    status_value=d.get("status") if d.get("status") in ("DRAFT","PROCESSED") else "DRAFT"

    conn=connect()
    try:
        cur=conn.cursor()
        cur.execute("""INSERT INTO salary_revisions(employee_id,effective_date,reason,note,status,created_by)
                       VALUES(?,?,?,?,?,?)""",
                    (eid,d.get("effective_date") or date.today().isoformat(),
                     d.get("reason") or "Salary adjustment",d.get("note",""),
                     status_value,current_user()["employee_id"]))
        rev=cur.lastrowid
        for c in components:
            name=str(c.get("name","")).strip()
            typ=str(c.get("type","EARNING")).upper()
            amount=float(c.get("amount",0) or 0)
            if not name or typ not in ("EARNING","DEDUCTION"):
                continue
            cur.execute("""INSERT INTO salary_components(revision_id,component_name,component_type,amount)
                           VALUES(?,?,?,?)""",(rev,name,typ,amount))
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
    return jsonify(ok=True, revision_id=rev)

@app.get("/api/documents/me")
@auth_required
def documents():
    return jsonify(documents=rows("""SELECT document_id,document_type,file_name,uploaded_at
                                     FROM employee_documents WHERE employee_id=? ORDER BY uploaded_at DESC""",
                                  (current_user()["employee_id"],)))

@app.get("/api/events")
@auth_required
def events():
    return jsonify(events=rows("""SELECT event_id,title,description,event_date,start_time,end_time
                                  FROM company_events ORDER BY event_date,event_id"""))

@app.post("/api/events")
@admin_required
def create_event():
    d=request.get_json(silent=True) or {}
    if not d.get("title") or not d.get("event_date"):
        return jsonify(error="Title and date are required"),400
    execute("""INSERT INTO company_events(title,description,event_date,created_by)
               VALUES(?,?,?,?)""",
            (d["title"],d.get("description",""),d["event_date"],current_user()["employee_id"]))
    return jsonify(ok=True),201

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.getenv("PORT","5000")), debug=True)
