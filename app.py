import os, sqlite3, secrets
from datetime import datetime, date
from functools import wraps
from flask import Flask, jsonify, request, session, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash

ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB=os.path.join(ROOT,"dayflow.db")
FRONT=os.path.join(ROOT,"frontend")
app=Flask(__name__)
app.secret_key=os.getenv("DAYFLOW_SECRET","dayflow-hackathon-change-me")
app.config.update(SESSION_COOKIE_HTTPONLY=True,SESSION_COOKIE_SAMESITE="Lax")

def conn():
    c=sqlite3.connect(DB); c.row_factory=sqlite3.Row; c.execute("PRAGMA foreign_keys=ON"); return c

def q(sql,p=(),one=False):
    c=conn();
    try:
        rows=c.execute(sql,p).fetchall(); out=[dict(r) for r in rows]
        return out[0] if one and out else (None if one else out)
    finally:c.close()

def run(sql,p=()):
    c=conn();
    try:
        cur=c.execute(sql,p);c.commit();return cur.lastrowid
    finally:c.close()

def user():
    eid=session.get('employee_id')
    if not eid:return None
    return q("SELECT e.*,d.department_name,a.password_hash FROM employees e LEFT JOIN departments d ON d.department_id=e.department_id JOIN user_accounts a ON a.employee_id=e.employee_id WHERE e.employee_id=?",(eid,),True)

def safe(u):
    if not u:return None
    x=dict(u);x.pop('password_hash',None);return x

def login_req(f):
    @wraps(f)
    def w(*a,**kw):
        if not user():return jsonify(error='Authentication required'),401
        return f(*a,**kw)
    return w

def admin_req(f):
    @wraps(f)
    def w(*a,**kw):
        u=user()
        if not u:return jsonify(error='Authentication required'),401
        if u['role']!='ADMIN':return jsonify(error='Admin access required'),403
        return f(*a,**kw)
    return w


def login_req(f):
    @wraps(f)
    def w(*a,**kw):
        if not user(): return jsonify(error="Authentication required"),401
        return f(*a,**kw)
    return w

def admin_req(f):
    @wraps(f)
    def w(*a,**kw):
        u=user()
        if not u: return jsonify(error="Authentication required"),401
        if u["role"]!="ADMIN": return jsonify(error="Admin access required"),403
        return f(*a,**kw)
    return w

def init_db():
    c=conn();
    with open(os.path.join(ROOT,'database','schema.sql'),encoding='utf-8') as f:c.executescript(f.read())
    c.commit();c.close()
    if q('SELECT employee_id FROM employees LIMIT 1',one=True):return
    for d in ['Engineering','Design','Finance','People Ops','Marketing','Sales']:run('INSERT INTO departments(department_name) VALUES(?)',(d,))
    for n,desc in [('Paid','Paid annual leave'),('Sick','Medical leave'),('Unpaid','Unpaid personal leave')]:run('INSERT INTO leave_types(leave_name,description) VALUES(?,?)',(n,desc))
    dept=lambda n:q('SELECT department_id FROM departments WHERE department_name=?',(n,),True)['department_id']
    people=[('OIAnSh2025001','Ananya','Sharma','ananya@dayflow.demo','+91 90000 10001',dept('Engineering'),'Software Engineer','2025-06-17','EMPLOYEE','Dayflow@123'),('OIRaMe2024002','Rahul','Menon','rahul@dayflow.demo','+91 90000 10002',dept('Design'),'Product Designer','2024-08-05','EMPLOYEE','Dayflow@123'),('OIPrNa2023003','Priya','Nair','priya@dayflow.demo','+91 90000 10003',dept('Finance'),'Finance Analyst','2023-01-09','EMPLOYEE','Dayflow@123'),('OIAdMi2020001','Admin','Manager','admin@dayflow.demo','+91 90000 19999',dept('People Ops'),'HR Administrator','2020-01-01','ADMIN','Admin@123')]
    for code,fn,ln,email,phone,dp,title,jd,role,pw in people:
        eid=run('INSERT INTO employees(employee_code,first_name,last_name,email,phone,location,department_id,job_title,joining_date,role) VALUES(?,?,?,?,?,?,?,?,?,?)',(code,fn,ln,email,phone,'Bengaluru',dp,title,jd,role));run('INSERT INTO user_accounts(employee_id,password_hash,must_change_password) VALUES(?,?,0)',(eid,generate_password_hash(pw)))
    comps={'OIAnSh2025001':[('Basic salary','EARNING',35100),('HRA','EARNING',15600),('Special allowance','EARNING',15600),('Other benefits','EARNING',11700),('Performance bonus','EARNING',5000),('Overtime','EARNING',2500),('PF','DEDUCTION',2000),('Professional tax','DEDUCTION',200),('Other deduction','DEDUCTION',500)],'OIRaMe2024002':[('Basic salary','EARNING',31050),('HRA','EARNING',13800),('Special allowance','EARNING',13800),('Other benefits','EARNING',10350),('Performance bonus','EARNING',3000),('PF','DEDUCTION',1800),('Professional tax','DEDUCTION',200)],'OIPrNa2023003':[('Basic salary','EARNING',27900),('HRA','EARNING',12400),('Special allowance','EARNING',12400),('Other benefits','EARNING',9300),('PF','DEDUCTION',1600),('Professional tax','DEDUCTION',200)]}
    for code,items in comps.items():
        eid=q('SELECT employee_id FROM employees WHERE employee_code=?',(code,),True)['employee_id'];rev=run('INSERT INTO salary_revisions(employee_id,effective_date,reason,status,created_by) VALUES(?,?,?,?,?)',(eid,'2026-01-01','Starting salary','PROCESSED',4));
        for n,t,a in items:run('INSERT INTO salary_components(revision_id,component_name,component_type,amount) VALUES(?,?,?,?)',(rev,n,t,a))
    # attendance seed, use recent demo dates
    for code,dt,ci,co,st in [('OIAnSh2025001','2026-08-21','09:04','18:06','PRESENT'),('OIAnSh2025001','2026-08-20','09:16','17:52','PRESENT'),('OIAnSh2025001','2026-08-19','09:02','13:12','HALF_DAY'),('OIRaMe2024002','2026-08-21','09:12','18:01','PRESENT'),('OIPrNa2023003','2026-08-21','10:01','18:04','PRESENT')]:
        eid=q('SELECT employee_id FROM employees WHERE employee_code=?',(code,),True)['employee_id'];run('INSERT INTO attendance(employee_id,attendance_date,check_in,check_out,status,verification_method,office_verified) VALUES(?,?,?,?,?,"OFFICE_CODE",1)',(eid,dt,ci,co,st))
    admin=4
    for code,typ,fd,td,reason,st,com in [('OIAnSh2025001','Paid','2026-09-03','2026-09-04','Family function','PENDING',''),('OIRaMe2024002','Sick','2026-08-27','2026-08-27','Medical appointment','APPROVED','Approved by HR'),('OIPrNa2023003','Unpaid','2026-09-10','2026-09-12','Personal work','REJECTED','Please discuss the dates with HR.')]:
        eid=q('SELECT employee_id FROM employees WHERE employee_code=?',(code,),True)['employee_id'];lt=q('SELECT leave_type_id FROM leave_types WHERE leave_name=?',(typ,),True)['leave_type_id'];run('INSERT INTO leave_requests(employee_id,leave_type_id,start_date,end_date,reason,status,reviewed_by,reviewed_at,reviewer_comment) VALUES(?,?,?,?,?,?,?,?,?)',(eid,lt,fd,td,reason,st,admin,datetime.now().isoformat() if st!='PENDING' else None,com or None))
    for t,d,dt in [('Team review','Weekly team review','2026-08-25'),('Payroll close','Monthly payroll processing','2026-08-28'),('Office town hall','People & operations meeting','2026-09-03')]:run('INSERT INTO company_events(title,description,event_date,created_by) VALUES(?,?,?,?)',(t,d,dt,admin))
    run('INSERT INTO office_settings(id,office_name,current_code,generated_at,rotation_seconds) VALUES(1,?,?,?,45)',('Bengaluru Main Office','DF-4821',datetime.now().isoformat()))

def office_code():
    row=q('SELECT * FROM office_settings WHERE id=1',one=True)
    age=(datetime.now()-datetime.fromisoformat(row['generated_at'])).total_seconds();remaining=max(0,int(row['rotation_seconds']-age))
    if remaining<=0:return rotate_code()
    return {**row,'remaining_seconds':remaining}

def rotate_code():
    code=f'DF-{secrets.randbelow(9000)+1000}';run('UPDATE office_settings SET current_code=?,generated_at=? WHERE id=1',(code,datetime.now().isoformat()));return office_code()

def payroll_view(eid):
    rev=q("SELECT * FROM salary_revisions WHERE employee_id=? AND status IN ('PROCESSED','DRAFT') ORDER BY effective_date DESC,revision_id DESC LIMIT 1",(eid,),True)
    if not rev:return {'gross_salary':0,'deductions':0,'net_salary':0,'annual_ctc':0,'components':[]}
    cs=q('SELECT component_name name,component_type type,amount FROM salary_components WHERE revision_id=? ORDER BY component_type,component_name',(rev['revision_id'],));g=sum(x['amount'] for x in cs if x['type']=='EARNING');d=sum(x['amount'] for x in cs if x['type']=='DEDUCTION');return {'revision_id':rev['revision_id'],'gross_salary':g,'deductions':d,'net_salary':g-d,'annual_ctc':g*12,'components':cs}

@app.get('/')
def index():return send_from_directory(FRONT,'index.html')
@app.get('/<path:path>')
def static_file(path):
    p=os.path.join(FRONT,path);return send_from_directory(FRONT,path) if os.path.isfile(p) else send_from_directory(FRONT,'index.html')
@app.post('/api/auth/login')
def auth_login():
    d=request.get_json() or {};v=(d.get('login') or '').strip();pw=d.get('password') or '';role=(d.get('role') or '').upper();u=q('SELECT e.*,d.department_name,a.password_hash FROM employees e LEFT JOIN departments d ON d.department_id=e.department_id JOIN user_accounts a ON a.employee_id=e.employee_id WHERE lower(e.employee_code)=lower(?) OR lower(e.email)=lower(?) LIMIT 1',(v,v),True)
    if not u or not check_password_hash(u['password_hash'],pw):return jsonify(error='The ID/email or password does not match.'),401
    if u['role']!=role:return jsonify(error='That account belongs to the other role.'),403
    session['employee_id']=u['employee_id'];run('UPDATE user_accounts SET last_login=? WHERE employee_id=?',(datetime.now().isoformat(),u['employee_id']));return jsonify(user=safe(u))
@app.post('/api/auth/register')
def auth_register():
    d=request.get_json() or {};fn=(d.get('first_name') or '').strip();ln=(d.get('last_name') or '').strip();email=(d.get('email') or '').strip();jd=d.get('joining_date') or '';role=(d.get('role') or 'EMPLOYEE').upper()
    if not fn or not ln or not email or not jd:return jsonify(error='Name, email and joining date are required'),400
    if role=='ADMIN' and d.get('admin_code')!=os.getenv('DAYFLOW_ADMIN_CODE','DAYFLOW-ADMIN'):return jsonify(error='Invalid HR invite code'),403
    if q('SELECT employee_id FROM employees WHERE lower(email)=lower(?)',(email,),True):return jsonify(error='Email already exists'),409
    y=jd[:4];serial=q("SELECT COUNT(*) n FROM employees WHERE substr(joining_date,1,4)=?",(y,),True)['n']+1;code=f"OI{fn[:2]}{ln[:2]}{y}{serial:03d}";temp=f"Df!{secrets.token_urlsafe(5)}9";dep=d.get('department') or 'General';row=q('SELECT department_id FROM departments WHERE department_name=?',(dep,),True);dep_id=row['department_id'] if row else run('INSERT INTO departments(department_name) VALUES(?)',(dep,));eid=run('INSERT INTO employees(employee_code,first_name,last_name,email,department_id,job_title,joining_date,role,location) VALUES(?,?,?,?,?,?,?,? ,"Bengaluru")',(code,fn,ln,email,dep_id,d.get('job_title') or 'Employee',jd,role));run('INSERT INTO user_accounts(employee_id,password_hash,must_change_password) VALUES(?,?,1)',(eid,generate_password_hash(temp)));rev=run('INSERT INTO salary_revisions(employee_id,effective_date,reason,status,created_by) VALUES(?,?,?,?,?)',(eid,jd,'Starting salary','PROCESSED',session.get('employee_id')));[run('INSERT INTO salary_components(revision_id,component_name,component_type,amount) VALUES(?,?,?,?)',(rev,n,'EARNING',a)) for n,a in [('Basic salary',22500),('HRA',10000),('Special allowance',10000),('Other benefits',7500)]];return jsonify(employee_code=code,temporary_password=temp),201
@app.post('/api/auth/logout')
def auth_logout():session.clear();return jsonify(ok=True)
@app.get('/api/auth/me')
def auth_me():u=user();return (jsonify(user=safe(u)),200) if u else (jsonify(error='Not signed in'),401)
@app.get('/api/dashboard')
@login_req
def dashboard():
    u=user();o=office_code()
    if u['role']=='ADMIN':
        staff=q("SELECT COUNT(*) n FROM employees WHERE role='EMPLOYEE' AND employment_status='ACTIVE'",one=True)['n'];present=q("SELECT COUNT(*) n FROM attendance WHERE attendance_date=? AND status='PRESENT'",(date.today().isoformat(),),one=True)['n'];pending=q("SELECT COUNT(*) n FROM leave_requests WHERE status='PENDING'",one=True)['n'];rows=q("SELECT employee_id FROM employees WHERE role='EMPLOYEE'");w=sum(payroll_view(x['employee_id'])['gross_salary'] for x in rows);req=q("SELECT lr.leave_request_id,CONCAT(e.first_name,' ',e.last_name) employee_name,lt.leave_name,lr.start_date,lr.end_date,lr.status FROM leave_requests lr JOIN employees e ON e.employee_id=lr.employee_id JOIN leave_types lt ON lt.leave_type_id=lr.leave_type_id WHERE lr.status='PENDING' ORDER BY lr.created_at DESC LIMIT 6");return jsonify(staff_count=staff,present_today=present,pending_leave=pending,monthly_wages=w,office_code=o['current_code'],office_remaining_seconds=o['remaining_seconds'],pending_requests=req)
    att=q("SELECT attendance_date,check_in,check_out,status,verification_method FROM attendance WHERE employee_id=? ORDER BY attendance_date DESC LIMIT 8",(u['employee_id'],));present=sum(1 for x in q("SELECT status FROM attendance WHERE employee_id=? AND status='PRESENT'",(u['employee_id'],)));p=payroll_view(u['employee_id']);leave=q("SELECT COALESCE(SUM(allocated_days-used_days),0) n FROM leave_balances WHERE employee_id=? AND leave_year='2026'",(u['employee_id'],),True)['n'];return jsonify(present_days=present,leave_remaining=leave,monthly_wage=p['gross_salary'],office_name=o['office_name'],recent_attendance=att)
@app.get('/api/employees')
@login_req
def employees():return jsonify(employees=q("SELECT e.employee_id,e.employee_code,e.first_name,e.last_name,e.email,e.phone,e.location,e.job_title,e.joining_date,e.role,e.employment_status,d.department_name FROM employees e LEFT JOIN departments d ON d.department_id=e.department_id WHERE e.role='EMPLOYEE' ORDER BY e.first_name,e.last_name"))
@app.get('/api/employees/me')
@login_req
def ememe():return jsonify(employee=safe(user()))
@app.get('/api/employees/<int:eid>')
@login_req
def employee_detail(eid):
    viewer=user();e=q("SELECT e.*,d.department_name FROM employees e LEFT JOIN departments d ON d.department_id=e.department_id WHERE e.employee_id=?",(eid,),True); 
    if not e:return jsonify(error='Employee not found'),404
    if viewer['role']!='ADMIN' and viewer['employee_id']!=eid:return jsonify(error='You can only view your own record'),403
    p=payroll_view(eid);e['salary']=p['gross_salary'];return jsonify(employee=e)
@app.patch('/api/employees/me')
@login_req
def emepatch():
    d=request.get_json() or {};run('UPDATE employees SET phone=?,location=? WHERE employee_id=?',(d.get('phone'),d.get('location'),user()['employee_id']));return jsonify(employee=safe(user()))
@app.post('/api/employees')
@admin_req
def add_employee():
    d=request.get_json() or {};fn=(d.get('first_name') or '').strip();ln=(d.get('last_name') or '').strip();email=(d.get('email') or '').strip();jd=d.get('joining_date') or '';
    if not fn or not ln or not email or not jd:return jsonify(error='Employee details are required'),400
    if q('SELECT employee_id FROM employees WHERE lower(email)=lower(?)',(email,),True):return jsonify(error='Email already exists'),409
    y=jd[:4];serial=q("SELECT COUNT(*) n FROM employees WHERE substr(joining_date,1,4)=?",(y,),True)['n']+1;code=f"OI{fn[:2]}{ln[:2]}{y}{serial:03d}";temp=f"Df!{secrets.token_urlsafe(5)}9";dep=d.get('department') or 'General';row=q('SELECT department_id FROM departments WHERE department_name=?',(dep,),True);dep_id=row['department_id'] if row else run('INSERT INTO departments(department_name) VALUES(?)',(dep,));eid=run('INSERT INTO employees(employee_code,first_name,last_name,email,department_id,job_title,joining_date,role,location) VALUES(?,?,?,?,?,?,?,"EMPLOYEE","Bengaluru")',(code,fn,ln,email,dep_id,d.get('job_title') or 'Employee',jd));run('INSERT INTO user_accounts(employee_id,password_hash,must_change_password) VALUES(?,?,1)',(eid,generate_password_hash(temp)));rev=run('INSERT INTO salary_revisions(employee_id,effective_date,reason,status,created_by) VALUES(?,?,?,?,?)',(eid,jd,'Starting salary','PROCESSED',user()['employee_id']));[run('INSERT INTO salary_components(revision_id,component_name,component_type,amount) VALUES(?,?,?,?)',(rev,n,'EARNING',a)) for n,a in [('Basic salary',22500),('HRA',10000),('Special allowance',10000),('Other benefits',7500)]];return jsonify(employee_code=code,temporary_password=temp),201
@app.get('/api/attendance/office-code')
@login_req
def office():o=office_code();return jsonify(code=o['current_code'],remaining_seconds=o['remaining_seconds'],office_name=o['office_name'])
@app.post('/api/attendance/office-code/rotate')
@admin_req
def office_rotate():o=rotate_code();return jsonify(code=o['current_code'],remaining_seconds=o['remaining_seconds'])
@app.post('/api/attendance/check-in')
@login_req
def checkin():
    u=user();d=request.get_json() or {};o=office_code();
    if u['role']!='EMPLOYEE':return jsonify(error='Only employees can use this check-in'),403
    if (d.get('office_code') or '').upper()!=o['current_code']:return jsonify(error='That office code is invalid or expired.'),400
    if q("SELECT attendance_id FROM attendance WHERE employee_id=? AND attendance_date=?",(u['employee_id'],date.today().isoformat()),True):return jsonify(error='Attendance is already marked today.'),409
    run("INSERT INTO attendance(employee_id,attendance_date,check_in,status,verification_method,office_verified,location_verified) VALUES(?,?,?,'PRESENT','OFFICE_CODE',1,?)",(u['employee_id'],date.today().isoformat(),datetime.now().strftime('%H:%M'),int(bool(d.get('location_verified')))));return jsonify(ok=True)
@app.get('/api/attendance')
@login_req
def attendance_api():
    u=user();rows=q("SELECT a.*,CONCAT(e.first_name,' ',e.last_name) employee_name FROM attendance a JOIN employees e ON e.employee_id=a.employee_id "+("WHERE a.employee_id=? " if u['role']!='ADMIN' else "")+"ORDER BY a.attendance_date DESC,a.check_in DESC",(u['employee_id'],) if u['role']!='ADMIN' else ());o=office_code();return jsonify(records=rows,present_count=sum(1 for x in rows if x['status']=='PRESENT'),half_day_count=sum(1 for x in rows if x['status']=='HALF_DAY'),office_code=o['current_code'],office_remaining_seconds=o['remaining_seconds'])
@app.get('/api/leave-types')
@login_req
def leave_types():return jsonify(types=q('SELECT leave_type_id,leave_name FROM leave_types ORDER BY leave_type_id'))
@app.get('/api/leaves')
@login_req
def leaves():
    u=user();
    if u['role']=='ADMIN':return jsonify(pending=q("SELECT lr.leave_request_id,CONCAT(e.first_name,' ',e.last_name) employee_name,lt.leave_name,lr.start_date,lr.end_date,lr.reason,lr.status,lr.reviewer_comment FROM leave_requests lr JOIN employees e ON e.employee_id=lr.employee_id JOIN leave_types lt ON lt.leave_type_id=lr.leave_type_id WHERE lr.status='PENDING' ORDER BY lr.created_at"))
    return jsonify(requests=q("SELECT lr.leave_request_id,lt.leave_name,lr.start_date,lr.end_date,lr.reason,lr.status,lr.reviewer_comment FROM leave_requests lr JOIN leave_types lt ON lt.leave_type_id=lr.leave_type_id WHERE lr.employee_id=? ORDER BY lr.created_at DESC",(u['employee_id'],)))
@app.post('/api/leaves')
@login_req
def leave_create():
    u=user();d=request.get_json() or {};run("INSERT INTO leave_requests(employee_id,leave_type_id,start_date,end_date,reason,status) VALUES(?,?,?,?,?,'PENDING')",(u['employee_id'],int(d['leave_type_id']),d['start_date'],d['end_date'],d.get('reason','')));return jsonify(ok=True),201
@app.patch('/api/leaves/<int:lid>/decision')
@admin_req
def leave_decision(lid):
    d=request.get_json() or {};dec=d.get('decision','').upper();
    if dec not in ('APPROVED','REJECTED'):return jsonify(error='Invalid decision'),400
    run('UPDATE leave_requests SET status=?,reviewed_by=?,reviewed_at=?,reviewer_comment=? WHERE leave_request_id=? AND status="PENDING"',(dec,user()['employee_id'],datetime.now().isoformat(),d.get('comment',''),lid));return jsonify(ok=True)
@app.get('/api/payroll')
@admin_req
def payroll_api():
    em=q("SELECT e.employee_id,e.employee_code,e.first_name,e.last_name,d.department_name FROM employees e LEFT JOIN departments d ON d.department_id=e.department_id WHERE e.role='EMPLOYEE'");records=[]
    for e in em:
        p=payroll_view(e['employee_id']);cs=p['components'];basic=next((c['amount'] for c in cs if c['name']=='Basic salary'),0);allow=sum(c['amount'] for c in cs if c['type']=='EARNING' and c['name'] not in ('Basic salary','Performance bonus','Overtime'));bonus=sum(c['amount'] for c in cs if c['name'] in ('Performance bonus','Overtime'));records.append({**e,'employee_name':e['first_name']+' '+e['last_name'],'basic_salary':basic,'allowances':allow,'bonus_overtime':bonus,'deductions':p['deductions'],'net_salary':p['net_salary']})
    revs=q("SELECT CONCAT(e.first_name,' ',e.last_name) employee_name,sr.effective_date,sr.reason,sr.status,(SELECT COALESCE(SUM(CASE WHEN sc.component_type='EARNING' THEN sc.amount ELSE 0 END),0) FROM salary_components sc WHERE sc.revision_id=sr.revision_id) gross_salary FROM salary_revisions sr JOIN employees e ON e.employee_id=sr.employee_id ORDER BY sr.created_at DESC LIMIT 10");return jsonify(records=records,total_gross=sum(x['basic_salary']+x['allowances']+x['bonus_overtime'] for x in records),total_net=sum(x['net_salary'] for x in records),revision_count=q('SELECT COUNT(*) n FROM salary_revisions',one=True)['n'],revisions=revs)
@app.get('/api/payroll/me')
@login_req
def payroll_me():
    p=payroll_view(user()['employee_id']);return jsonify(record=p,components=p['components'])
@app.get('/api/payroll/<int:eid>')
@admin_req
def payroll_detail(eid):
    e=q('SELECT e.*,d.department_name FROM employees e LEFT JOIN departments d ON d.department_id=e.department_id WHERE e.employee_id=?',(eid,),True);
    if not e:return jsonify(error='Employee not found'),404
    p=payroll_view(eid);return jsonify(employee=e,gross_salary=p['gross_salary'],deductions=p['deductions'],net_salary=p['net_salary'],annual_ctc=p['annual_ctc'],components=p['components'])
@app.put('/api/payroll/<int:eid>')
@admin_req
def payroll_update(eid):
    d=request.get_json() or {};components=d.get('components') or [];status=d.get('status','DRAFT');
    if not components:return jsonify(error='At least one component is required'),400
    rev=run('INSERT INTO salary_revisions(employee_id,effective_date,reason,note,status,created_by) VALUES(?,?,?,?,?,?)',(eid,d.get('effective_date') or date.today().isoformat(),d.get('reason') or 'Salary adjustment',d.get('note',''),status,user()['employee_id']))
    for c in components:
        if not c.get('name'):continue
        run('INSERT INTO salary_components(revision_id,component_name,component_type,amount) VALUES(?,?,?,?)',(rev,c['name'],c.get('type','EARNING'),float(c.get('amount',0))))
    return jsonify(ok=True,revision_id=rev)
@app.get('/api/documents/me')
@login_req
def docs():return jsonify(documents=q('SELECT document_id,document_type,file_name,uploaded_at FROM employee_documents WHERE employee_id=? ORDER BY uploaded_at DESC',(user()['employee_id'],)))
@app.get('/api/events')
@login_req
def events():return jsonify(events=q('SELECT event_id,title,description,event_date,start_time,end_time FROM company_events ORDER BY event_date,event_id'))
@app.post('/api/events')
@admin_req
def add_event():
    d=request.get_json() or {};run('INSERT INTO company_events(title,description,event_date,created_by) VALUES(?,?,?,?)',(d['title'],d.get('description',''),d['event_date'],user()['employee_id']));return jsonify(ok=True),201
@app.errorhandler(Exception)
def err(e):app.logger.exception(e);return jsonify(error='Server error. Check the backend terminal.'),500

if __name__=='__main__':init_db();app.run(host='127.0.0.1',port=int(os.getenv('PORT','5000')),debug=True)
