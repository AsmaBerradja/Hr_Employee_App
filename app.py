from datetime import datetime
import os
from flask import (
    Flask,
    flash,
    redirect,
    render_template_string,
    request,
    session,
    url_for,
)
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "retainpro_super_secret_key"

UPLOAD_FOLDER = os.path.join("static", "uploads")
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

basedir = os.path.abspath(os.path.dirname(__file__))
app.config["SQLALCHEMY_DATABASE_URI"] = (
    "sqlite:///" + os.path.join(basedir, "retainpro.db")
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


# 1. نموذج المستخدمين
class User(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  username = db.Column(db.String(80), unique=True, nullable=False)
  password = db.Column(db.String(120), nullable=False)
  role = db.Column(db.String(20), nullable=False)
  name = db.Column(db.String(100), nullable=False)
  position = db.Column(db.String(100), default="Staff")
  avatar = db.Column(db.String(300), default="")
  dob = db.Column(db.String(50), default="")
  national_id = db.Column(db.String(50), default="")
  bank_account = db.Column(db.String(50), default="")


# 2. نموذج قاعدة البيانات لربط وحفظ كل طلبات وخانات الموظف
class RequestItem(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  category = db.Column(
      db.String(50), nullable=False
  )  # complaint, question, survey, talent
  employee_name = db.Column(db.String(100), nullable=False)
  title = db.Column(db.String(200), nullable=False)
  details = db.Column(db.Text, nullable=False)
  date_submitted = db.Column(db.String(50), nullable=False)


with app.app_context():
  db.create_all()
  if not User.query.filter_by(username="admin").first():
    admin_user = User(
        username="admin",
        password="hr123password",
        role="hr",
        name="HR Manager",
        position="Head of HR",
    )
    emp_user = User(
        username="emp001",
        password="employee123",
        role="employee",
        name="John Doe",
        position="Software Developer",
        dob="1995-06-15",
        national_id="123456789012",
        bank_account="RIB 00123456789",
    )
    db.session.add(admin_user)
    db.session.add(emp_user)
    db.session.commit()

# HR Layout
BASE_LAYOUT_HR = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{{ title }} - RetainPro</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
        body { background: #f8fafc; display: flex; height: 100vh; overflow: hidden; }
        .sidebar { width: 260px; background: #1e1b4b; color: white; display: flex; flex-direction: column; padding: 24px 16px; flex-shrink: 0; }
        .logo-box { font-size: 20px; font-weight: bold; display: flex; align-items: center; gap: 10px; margin-bottom: 35px; padding-left: 10px; color: white; }
        .sidebar a { color: #94a3b8; text-decoration: none; padding: 12px 16px; border-radius: 10px; margin-bottom: 6px; font-size: 14px; font-weight: 500; transition: 0.2s; display: flex; align-items: center; gap: 12px; }
        .sidebar a:hover, .sidebar a.active { background: #4f46e5; color: white; }
        .logout-btn { margin-top: auto; background: rgba(255, 255, 255, 0.08); color: #ffffff !important; border: 1px solid rgba(255, 255, 255, 0.15); }
        .logout-btn:hover { background: #4f46e5 !important; color: #ffffff !important; }
        .main-container { flex: 1; padding: 30px 50px; overflow-y: auto; display: flex; flex-direction: column; }
        .top-nav { display: flex; justify-content: flex-end; align-items: center; gap: 20px; margin-bottom: 25px; position: relative; }
        .notification-icon { font-size: 16px; cursor: pointer; color: #ffffff; background: #4f46e5; padding: 10px; border-radius: 50%; box-shadow: 0 2px 6px rgba(79, 70, 229, 0.3); display: flex; align-items: center; justify-content: center; transition: 0.2s; }
        .notification-icon:hover { background: #4338ca; }
        .profile-dropdown { position: relative; display: inline-block; }
        .user-profile { display: flex; align-items: center; gap: 8px; font-weight: 600; color: #1e1b4b; font-size: 14px; background: white; padding: 6px 14px; border-radius: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.02); cursor: pointer; border: 1px solid #e2e8f0; }
        .user-profile img { width: 28px; height: 28px; border-radius: 50%; object-fit: cover; }
        .dropdown-content { display: none; position: absolute; right: 0; background-color: #ffffff; min-width: 180px; box-shadow: 0px 8px 16px rgba(0,0,0,0.08); border-radius: 12px; z-index: 100; overflow: hidden; border: 1px solid #e2e8f0; margin-top: 8px; }
        .dropdown-content a { color: #334155; padding: 12px 16px; text-decoration: none; display: flex; align-items: center; gap: 10px; font-size: 14px; transition: 0.2s; margin-bottom: 0; }
        .dropdown-content a:hover { background-color: #f1f5f9; color: #4f46e5; }
        .profile-dropdown:hover .dropdown-content { display: block; }
        .page-card { background: white; border-radius: 14px; padding: 35px 40px; border: 1px solid #e2e8f0; box-shadow: 0 4px 12px rgba(0,0,0,0.03); max-width: 1000px; width: 100%; margin: 0 auto; }
        .btn-primary { background: #4f46e5; color: white; border: none; padding: 13px 20px; border-radius: 8px; font-size: 15px; font-weight: 600; cursor: pointer; transition: 0.2s; }
        .btn-primary:hover { background: #4338ca; }
    </style>
</head>
<body>
    <div class="sidebar">
        <div class="logo-box"><span><i class="fa-solid fa-users-rectangle"></i></span> RetainPro</div>
        <a href="/hr-dashboard" class="{{ 'active' if active_page == 'home' else '' }}"><i class="fa-solid fa-house"></i> Home</a>
        <a href="/hr/add-employee" class="{{ 'active' if active_page == 'add' else '' }}"><i class="fa-solid fa-user-plus"></i> Add New Employee</a>
        <a href="/hr/employees" class="{{ 'active' if active_page == 'employees' else '' }}"><i class="fa-solid fa-address-book"></i> All Employees</a>
        <a href="/hr/complaints" class="{{ 'active' if active_page == 'complaints' else '' }}"><i class="fa-solid fa-triangle-exclamation"></i> Employee Complaints</a>
        <a href="/hr/surveys" class="{{ 'active' if active_page == 'surveys' else '' }}"><i class="fa-solid fa-chart-bar"></i> Employee Surveys</a>
        <a href="/hr/questions" class="{{ 'active' if active_page == 'questions' else '' }}"><i class="fa-solid fa-circle-question"></i> Employee Questions</a>
        <a href="/hr/talents" class="{{ 'active' if active_page == 'talents' else '' }}"><i class="fa-solid fa-graduation-cap"></i> Talent & Internship</a>
        <a href="/logout" class="logout-btn"><i class="fa-solid fa-right-from-bracket"></i> Logout</a>
    </div>
    <div class="main-container">
        <div class="top-nav">
            <div class="notification-icon" title="Notifications"><i class="fa-solid fa-bell"></i></div>
            <div class="profile-dropdown">
                <div class="user-profile">
                    {% if current_user.avatar %}
                        <img src="{{ current_user.avatar }}" alt="Avatar">
                    {% else %}
                        <img src="https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=150&q=80" alt="Avatar">
                    {% endif %}
                    {{ current_user.name }} ▾
                </div>
                <div class="dropdown-content">
                    <a href="/hr/profile"><i class="fa-solid fa-user-gear"></i> Profile Settings</a>
                    <a href="/logout" style="color: #ef4444;"><i class="fa-solid fa-right-from-bracket"></i> Logout</a>
                </div>
            </div>
        </div>
        HR_CONTENT_PLACEHOLDER
    </div>
</body>
</html>
"""

# Employee Layout
BASE_LAYOUT_EMPLOYEE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{{ title }} - RetainPro Employee Portal</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
        body { background: #f8fafc; display: flex; height: 100vh; overflow: hidden; }
        .sidebar { width: 260px; background: #1e1b4b; color: white; display: flex; flex-direction: column; padding: 24px 16px; flex-shrink: 0; }
        .logo-box { font-size: 20px; font-weight: bold; display: flex; align-items: center; gap: 10px; margin-bottom: 35px; padding-left: 10px; color: white; }
        .sidebar a { color: #94a3b8; text-decoration: none; padding: 12px 16px; border-radius: 10px; margin-bottom: 6px; font-size: 14px; font-weight: 500; transition: 0.2s; display: flex; align-items: center; gap: 12px; }
        .sidebar a:hover, .sidebar a.active { background: #4f46e5; color: white; }
        .logout-btn { margin-top: auto; background: rgba(255, 255, 255, 0.08); color: #ffffff !important; border: 1px solid rgba(255, 255, 255, 0.15); }
        .logout-btn:hover { background: #4f46e5 !important; color: #ffffff !important; }
        .main-container { flex: 1; padding: 30px 50px; overflow-y: auto; display: flex; flex-direction: column; }
        .top-nav { display: flex; justify-content: flex-end; align-items: center; gap: 20px; margin-bottom: 25px; position: relative; }
        .notification-icon { font-size: 16px; cursor: pointer; color: #ffffff; background: #4f46e5; padding: 10px; border-radius: 50%; box-shadow: 0 2px 6px rgba(79, 70, 229, 0.3); display: flex; align-items: center; justify-content: center; transition: 0.2s; }
        .notification-icon:hover { background: #4338ca; }
        .profile-dropdown { position: relative; display: inline-block; }
        .user-profile { display: flex; align-items: center; gap: 8px; font-weight: 600; color: #1e1b4b; font-size: 14px; background: white; padding: 6px 14px; border-radius: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.02); cursor: pointer; border: 1px solid #e2e8f0; }
        .user-profile img { width: 28px; height: 28px; border-radius: 50%; object-fit: cover; }
        .dropdown-content { display: none; position: absolute; right: 0; background-color: #ffffff; min-width: 180px; box-shadow: 0px 8px 16px rgba(0,0,0,0.08); border-radius: 12px; z-index: 100; overflow: hidden; border: 1px solid #e2e8f0; margin-top: 8px; }
        .dropdown-content a { color: #334155; padding: 12px 16px; text-decoration: none; display: flex; align-items: center; gap: 10px; font-size: 14px; transition: 0.2s; margin-bottom: 0; }
        .dropdown-content a:hover { background-color: #f1f5f9; color: #4f46e5; }
        .profile-dropdown:hover .dropdown-content { display: block; }
        .page-card { background: white; border-radius: 14px; padding: 35px 40px; border: 1px solid #e2e8f0; box-shadow: 0 4px 12px rgba(0,0,0,0.03); max-width: 900px; width: 100%; margin: 0 auto; }
        .btn-primary { background: #4f46e5; color: white; border: none; padding: 13px 20px; border-radius: 8px; font-size: 15px; font-weight: 600; cursor: pointer; transition: 0.2s; }
        .btn-primary:hover { background: #4338ca; }
    </style>
</head>
<body>
    <div class="sidebar">
        <div class="logo-box"><span><i class="fa-solid fa-user-tie"></i></span> Employee Hub</div>
        <a href="/employee-dashboard" class="{{ 'active' if active_page == 'home' else '' }}"><i class="fa-solid fa-house"></i> Dashboard</a>
        <a href="/employee/profile" class="{{ 'active' if active_page == 'profile' else '' }}"><i class="fa-solid fa-id-card"></i> My Profile & Info</a>
        <a href="/employee/complaint" class="{{ 'active' if active_page == 'complaint' else '' }}"><i class="fa-solid fa-triangle-exclamation"></i> Submit Complaint</a>
        <a href="/employee/surveys" class="{{ 'active' if active_page == 'surveys' else '' }}"><i class="fa-solid fa-square-poll-vertical"></i> Surveys & Feedback</a>
        <a href="/employee/ask-hr" class="{{ 'active' if active_page == 'ask-hr' else '' }}"><i class="fa-solid fa-comments"></i> Ask HR Manager</a>
        <a href="/employee/talents" class="{{ 'active' if active_page == 'talents' else '' }}"><i class="fa-solid fa-graduation-cap"></i> Talent & Internships</a>
        <a href="/logout" class="logout-btn"><i class="fa-solid fa-right-from-bracket"></i> Logout</a>
    </div>
    <div class="main-container">
        <div class="top-nav">
            <div class="notification-icon" title="Notifications"><i class="fa-solid fa-bell"></i></div>
            <div class="profile-dropdown">
                <div class="user-profile">
                    {% if current_user.avatar %}
                        <img src="{{ current_user.avatar }}" alt="Avatar">
                    {% else %}
                        <img src="https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=150&q=80" alt="Avatar">
                    {% endif %}
                    {{ current_user.name }} ▾
                </div>
                <div class="dropdown-content">
                    <a href="/employee/profile"><i class="fa-solid fa-user-gear"></i> Profile Settings</a>
                    <a href="/logout" style="color: #ef4444;"><i class="fa-solid fa-right-from-bracket"></i> Logout</a>
                </div>
            </div>
        </div>
        EMPLOYEE_CONTENT_PLACEHOLDER
    </div>
</body>
</html>
"""

LOGIN_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>RetainPro - Portal Access</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
        body { background: #f8fafc; display: flex; height: 100vh; overflow: hidden; }
        .hero-side { flex: 1.2; background: linear-gradient(135deg, rgba(30, 27, 75, 0.85), rgba(79, 70, 229, 0.75)), url('https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?auto=format&fit=crop&w=1200&q=80') no-repeat center center/cover; display: flex; flex-direction: column; justify-content: flex-end; padding: 60px; color: white; position: relative; }
        .hero-content h1 { font-size: 42px; font-weight: 700; line-height: 1.2; margin-bottom: 15px; }
        .hero-content p { font-size: 16px; opacity: 0.9; }
        .logo-area { position: absolute; top: 40px; left: 60px; display: flex; align-items: center; gap: 10px; font-weight: 700; font-size: 20px; }
        .form-side { flex: 1; background: #ffffff; display: flex; flex-direction: column; justify-content: center; align-items: center; padding: 40px; box-shadow: -10px 0 30px rgba(0,0,0,0.03); z-index: 10; }
        .form-container { width: 100%; max-width: 380px; }
        .form-header h2 { font-size: 26px; color: #1e1b4b; font-weight: 700; margin-bottom: 8px; }
        .form-header p { font-size: 14px; color: #64748b; margin-bottom: 25px; }
        .role-cards { display: flex; flex-direction: column; gap: 12px; margin-bottom: 20px; }
        .role-card { display: flex; align-items: center; justify-content: space-between; padding: 16px 20px; border: 2px solid #e2e8f0; border-radius: 12px; cursor: pointer; transition: all 0.2s ease; background: #fff; text-decoration: none; }
        .role-card:hover { border-color: #6366f1; background: #f8fafc; }
        .role-info h4 { font-size: 15px; color: #1e1b4b; font-weight: 600; }
        .role-info p { font-size: 12px; color: #64748b; margin-top: 2px; }
        .role-icon { width: 36px; height: 36px; background: #eef2ff; color: #4f46e5; border-radius: 8px; display: flex; align-items: center; justify-content: center; font-weight: bold; }
        .input-group { margin-bottom: 16px; }
        .input-group label { display: block; font-size: 13px; font-weight: 600; color: #334155; margin-bottom: 6px; }
        .input-group input { width: 100%; padding: 12px 14px; border: 1px solid #cbd5e1; border-radius: 8px; font-size: 14px; outline: none; }
        .btn-primary { width: 100%; padding: 13px; background: #4f46e5; color: white; border: none; border-radius: 8px; font-size: 15px; font-weight: 600; cursor: pointer; transition: background 0.2s; margin-top: 5px; }
        .btn-primary:hover { background: #4338ca; }
        .back-link { display: inline-block; margin-top: 15px; font-size: 13px; color: #4f46e5; text-decoration: none; font-weight: 600; }
        .error-box { background: #fee2e2; color: #991b1b; padding: 10px; border-radius: 8px; font-size: 13px; margin-bottom: 15px; text-align: center; }
    </style>
</head>
<body>
    <div class="hero-side">
        <div class="logo-area"><span><i class="fa-solid fa-users"></i></span> RetainPro</div>
        <div class="hero-content">
            <h1>Your Voice Builds a Better Workplace</h1>
            <p>Manage your team data, review workflows, and streamline human resources effortlessly.</p>
        </div>
    </div>
    <div class="form-side">
        <div class="form-container">
            {% if step == 'select' %}
                <div class="form-header">
                    <h2>Welcome to RetainPro</h2>
                    <p>Choose your access type to continue</p>
                </div>
                <div class="role-cards">
                    <a href="/login-form?role=employee" class="role-card">
                        <div style="display: flex; align-items: center; gap: 15px;">
                            <div class="role-icon"><i class="fa-solid fa-user"></i></div>
                            <div class="role-info"><h4>Employee</h4><p>Access surveys, view tasks & info</p></div>
                        </div>
                        <span><i class="fa-solid fa-chevron-right"></i></span>
                    </a>
                    <a href="/login-form?role=hr" class="role-card">
                        <div style="display: flex; align-items: center; gap: 15px;">
                            <div class="role-icon"><i class="fa-solid fa-shield-halved"></i></div>
                            <div class="role-info"><h4>HR Manager</h4><p>Manage data and view reports</p></div>
                        </div>
                        <span><i class="fa-solid fa-chevron-right"></i></span>
                    </a>
                </div>
            {% else %}
                <div class="form-header">
                    <h2>{{ 'HR Manager' if role == 'hr' else 'Employee' }} Login</h2>
                    <p>Enter your credentials to access your account</p>
                </div>
                {% if error %}<div class="error-box">{{ error }}</div>{% endif %}
                <form method="POST" action="/authenticate">
                    <input type="hidden" name="role" value="{{ role }}">
                    <div class="input-group"><label>Username / ID</label><input type="text" name="username" placeholder="Enter username" required></div>
                    <div class="input-group"><label>Password</label><input type="password" name="password" placeholder="••••••••" required></div>
                    <button type="submit" class="btn-primary">Login</button>
                </form>
                <a class="back-link" href="/">← Back to role selection</a>
            {% endif %}
        </div>
    </div>
</body>
</html>
"""

HR_HOME_CONTENT = """
<div class="welcome-section" style="margin-bottom: 25px;">
    <h1 style="font-size: 26px; color: #1e1b4b; font-weight: 700;">Welcome back, {{ current_user.name }}! 👋</h1>
    <p style="font-size: 14px; color: #64748b; margin-top: 4px;">Manage your team data, track workflows, and build a better workplace.</p>
</div>

<div style="display: grid; grid-template-columns: 2.2fr 1fr; gap: 24px; align-items: start;">
    <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 16px;">
        <a href="/hr/add-employee" style="background: white; padding: 18px 20px; border-radius: 14px; border: 1px solid #e2e8f0; text-decoration: none; transition: 0.2s;" onmouseover="this.style.borderColor='#6366f1'" onmouseout="this.style.borderColor='#e2e8f0'">
            <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
                <div style="width: 38px; height: 38px; border-radius: 10px; background: #eef2ff; color: #4f46e5; display: flex; align-items: center; justify-content: center;"><i class="fa-solid fa-user-plus"></i></div>
                <span style="color: #94a3b8;"><i class="fa-solid fa-arrow-right"></i></span>
            </div>
            <h3 style="font-size: 15px; color: #1e1b4b; font-weight: 600;">Add New Employee</h3>
            <p style="font-size: 12px; color: #64748b; margin-top: 3px;">Register staff & assign credentials</p>
        </a>

        <a href="/hr/employees" style="background: white; padding: 18px 20px; border-radius: 14px; border: 1px solid #e2e8f0; text-decoration: none; transition: 0.2s;" onmouseover="this.style.borderColor='#6366f1'" onmouseout="this.style.borderColor='#e2e8f0'">
            <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
                <div style="width: 38px; height: 38px; border-radius: 10px; background: #eef2ff; color: #4f46e5; display: flex; align-items: center; justify-content: center;"><i class="fa-solid fa-users"></i></div>
                <span style="color: #94a3b8;"><i class="fa-solid fa-arrow-right"></i></span>
            </div>
            <h3 style="font-size: 15px; color: #1e1b4b; font-weight: 600;">All Employees</h3>
            <p style="font-size: 12px; color: #64748b; margin-top: 3px;">View active company staff profiles</p>
        </a>

        <a href="/hr/complaints" style="background: white; padding: 18px 20px; border-radius: 14px; border: 1px solid #e2e8f0; text-decoration: none; transition: 0.2s;" onmouseover="this.style.borderColor='#6366f1'" onmouseout="this.style.borderColor='#e2e8f0'">
            <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
                <div style="width: 38px; height: 38px; border-radius: 10px; background: #eef2ff; color: #4f46e5; display: flex; align-items: center; justify-content: center;"><i class="fa-solid fa-triangle-exclamation"></i></div>
                <span style="color: #94a3b8;"><i class="fa-solid fa-arrow-right"></i></span>
            </div>
            <h3 style="font-size: 15px; color: #1e1b4b; font-weight: 600;">Employee Complaints</h3>
            <p style="font-size: 12px; color: #64748b; margin-top: 3px;">Review and resolve staff issues</p>
        </a>

        <a href="/hr/surveys" style="background: white; padding: 18px 20px; border-radius: 14px; border: 1px solid #e2e8f0; text-decoration: none; transition: 0.2s;" onmouseover="this.style.borderColor='#6366f1'" onmouseout="this.style.borderColor='#e2e8f0'">
            <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
                <div style="width: 38px; height: 38px; border-radius: 10px; background: #eef2ff; color: #4f46e5; display: flex; align-items: center; justify-content: center;"><i class="fa-solid fa-square-poll-vertical"></i></div>
                <span style="color: #94a3b8;"><i class="fa-solid fa-arrow-right"></i></span>
            </div>
            <h3 style="font-size: 15px; color: #1e1b4b; font-weight: 600;">Employee Surveys</h3>
            <p style="font-size: 12px; color: #64748b; margin-top: 3px;">Analyze workplace satisfaction</p>
        </a>

        <a href="/hr/questions" style="background: white; padding: 18px 20px; border-radius: 14px; border: 1px solid #e2e8f0; text-decoration: none; transition: 0.2s;" onmouseover="this.style.borderColor='#6366f1'" onmouseout="this.style.borderColor='#e2e8f0'">
            <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
                <div style="width: 38px; height: 38px; border-radius: 10px; background: #eef2ff; color: #4f46e5; display: flex; align-items: center; justify-content: center;"><i class="fa-solid fa-comments"></i></div>
                <span style="color: #94a3b8;"><i class="fa-solid fa-arrow-right"></i></span>
            </div>
            <h3 style="font-size: 15px; color: #1e1b4b; font-weight: 600;">Employee Questions</h3>
            <p style="font-size: 12px; color: #64748b; margin-top: 3px;">Answer inquiries & support tickets</p>
        </a>

        <a href="/hr/talents" style="background: white; padding: 18px 20px; border-radius: 14px; border: 1px solid #e2e8f0; text-decoration: none; transition: 0.2s;" onmouseover="this.style.borderColor='#6366f1'" onmouseout="this.style.borderColor='#e2e8f0'">
            <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
                <div style="width: 38px; height: 38px; border-radius: 10px; background: #eef2ff; color: #4f46e5; display: flex; align-items: center; justify-content: center;"><i class="fa-solid fa-bullseye"></i></div>
                <span style="color: #94a3b8;"><i class="fa-solid fa-arrow-right"></i></span>
            </div>
            <h3 style="font-size: 15px; color: #1e1b4b; font-weight: 600;">Talent & Internship Requests</h3>
            <p style="font-size: 12px; color: #64748b; margin-top: 3px;">Manage training & trainee requests</p>
        </a>
    </div>

    <div style="background: white; padding: 20px; border-radius: 14px; border: 1px solid #e2e8f0;">
        <h4 style="font-size: 15px; color: #1e1b4b; margin-bottom: 8px;"><i class="fa-solid fa-shield-halved" style="color: #4f46e5;"></i> System Status</h4>
        <p style="font-size: 13px; color: #64748b; margin-bottom: 12px;">Database active & secure via SQLite. All core management tools are running smoothly.</p>
        <a href="/hr/employees" style="display: block; text-align: center; background: #4f46e5; color: white; padding: 10px; border-radius: 8px; text-decoration: none; font-size: 13px; font-weight: 600;">View Staff List</a>
    </div>
</div>
"""

PROFILE_CONTENT = """
<div class="page-card">
    <h2 style="color: #1e1b4b; margin-bottom: 25px; display: flex; align-items: center; gap: 10px;"><i class="fa-solid fa-user-gear"></i> Profile Settings</h2>
    
    {% if msg %}
    <p style="color: #10b981; font-size: 13px; margin-bottom: 20px; font-weight: 600;">{{ msg }}</p>
    {% endif %}

    <form method="POST" enctype="multipart/form-data">
        <div style="text-align: center; margin-bottom: 25px;">
            {% if current_user.avatar %}
                <img src="{{ current_user.avatar }}" alt="Avatar" style="width: 90px; height: 90px; border-radius: 50%; object-fit: cover; border: 3px solid #4f46e5;">
            {% else %}
                <img src="https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=150&q=80" alt="Avatar" style="width: 90px; height: 90px; border-radius: 50%; object-fit: cover; border: 3px solid #4f46e5;">
            {% endif %}
        </div>

        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px;">
            <div>
                <label style="display: block; font-size: 13px; font-weight: 600; color: #334155; margin-bottom: 6px;">Full Name</label>
                <input type="text" name="name" value="{{ current_user.name }}" required style="width: 100%; padding: 12px; border: 1px solid #cbd5e1; border-radius: 8px; font-size: 14px;">
            </div>
            <div>
                <label style="display: block; font-size: 13px; font-weight: 600; color: #334155; margin-bottom: 6px;">New Password (leave blank if unchanged)</label>
                <input type="password" name="password" placeholder="••••••••" style="width: 100%; padding: 12px; border: 1px solid #cbd5e1; border-radius: 8px; font-size: 14px;">
            </div>
        </div>

        <div style="margin-bottom: 25px;">
            <label style="display: block; font-size: 13px; font-weight: 600; color: #334155; margin-bottom: 6px;">Upload New Profile Picture (from computer)</label>
            <input type="file" name="avatar_file" accept="image/*" style="width: 100%; padding: 10px; border: 1px solid #cbd5e1; border-radius: 8px; background: #f8fafc; font-size: 14px;">
        </div>

        <button type="submit" class="btn-primary" style="width: 100%;">Save Changes</button>
    </form>
</div>
"""

ADD_EMPLOYEE_CONTENT = """
<div class="page-card">
    <h2 style="color: #1e1b4b; margin-bottom: 25px;"><i class="fa-solid fa-user-plus"></i> Add New Employee</h2>
    {% if msg %}<p style="color: green; font-size: 13px; margin-bottom: 15px; font-weight: 600;">{{ msg }}</p>{% endif %}
    
    <form method="POST" enctype="multipart/form-data">
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px;">
            <div>
                <label style="display: block; font-size: 13px; font-weight: 600; color: #334155; margin-bottom: 6px;">Full Name</label>
                <input type="text" name="name" required placeholder="e.g. Sarah Smith" style="width: 100%; padding: 12px; border: 1px solid #cbd5e1; border-radius: 8px; font-size: 14px;">
            </div>
            <div>
                <label style="display: block; font-size: 13px; font-weight: 600; color: #334155; margin-bottom: 6px;">Date of Birth</label>
                <input type="date" name="dob" required style="width: 100%; padding: 12px; border: 1px solid #cbd5e1; border-radius: 8px; font-size: 14px;">
            </div>
        </div>

        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px;">
            <div>
                <label style="display: block; font-size: 13px; font-weight: 600; color: #334155; margin-bottom: 6px;">National ID Number</label>
                <input type="text" name="national_id" required placeholder="e.g. 123456789012" style="width: 100%; padding: 12px; border: 1px solid #cbd5e1; border-radius: 8px; font-size: 14px;">
            </div>
            <div>
                <label style="display: block; font-size: 13px; font-weight: 600; color: #334155; margin-bottom: 6px;">Bank Account Number</label>
                <input type="text" name="bank_account" required placeholder="e.g. RIB 00123456789" style="width: 100%; padding: 12px; border: 1px solid #cbd5e1; border-radius: 8px; font-size: 14px;">
            </div>
        </div>

        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px;">
            <div>
                <label style="display: block; font-size: 13px; font-weight: 600; color: #334155; margin-bottom: 6px;">Username / ID</label>
                <input type="text" name="username" required placeholder="e.g. emp002" style="width: 100%; padding: 12px; border: 1px solid #cbd5e1; border-radius: 8px; font-size: 14px;">
            </div>
            <div>
                <label style="display: block; font-size: 13px; font-weight: 600; color: #334155; margin-bottom: 6px;">Password</label>
                <input type="password" name="password" required placeholder="••••••••" style="width: 100%; padding: 12px; border: 1px solid #cbd5e1; border-radius: 8px; font-size: 14px;">
            </div>
        </div>

        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 25px;">
            <div>
                <label style="display: block; font-size: 13px; font-weight: 600; color: #334155; margin-bottom: 6px;">Job Position</label>
                <input type="text" name="position" required placeholder="e.g. UI/UX Designer" style="width: 100%; padding: 12px; border: 1px solid #cbd5e1; border-radius: 8px; font-size: 14px;">
            </div>
            <div>
                <label style="display: block; font-size: 13px; font-weight: 600; color: #334155; margin-bottom: 6px;">Employee Photo</label>
                <input type="file" name="avatar_file" accept="image/*" style="width: 100%; padding: 10px; border: 1px solid #cbd5e1; border-radius: 8px; background: #f8fafc; font-size: 14px;">
            </div>
        </div>

        <button type="submit" class="btn-primary" style="width: 100%;">Register Employee</button>
    </form>
</div>
"""

ALL_EMPLOYEES_CONTENT = """
<div class="page-card" style="max-width: 1100px;">
    <h2 style="color: #1e1b4b; margin-bottom: 20px;"><i class="fa-solid fa-users"></i> All Company Employees</h2>
    <table style="width: 100%; border-collapse: collapse;">
        <thead>
            <tr style="background: #f8fafc; border-bottom: 2px solid #e2e8f0;">
                <th style="padding: 12px; text-align: left; color: #475569;">Photo</th>
                <th style="padding: 12px; text-align: left; color: #475569;">Full Name</th>
                <th style="padding: 12px; text-align: left; color: #475569;">Username</th>
                <th style="padding: 12px; text-align: left; color: #475569;">DOB</th>
                <th style="padding: 12px; text-align: left; color: #475569;">National ID</th>
                <th style="padding: 12px; text-align: left; color: #475569;">Bank Account</th>
                <th style="padding: 12px; text-align: left; color: #475569;">Position</th>
            </tr>
        </thead>
        <tbody>
            {% for emp in employees %}
            <tr style="border-bottom: 1px solid #e2e8f0;">
                <td style="padding: 12px;">
                    {% if emp.avatar %}
                        <img src="{{ emp.avatar }}" style="width: 35px; height: 35px; border-radius: 50%; object-fit: cover;">
                    {% else %}
                        <img src="https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=150&q=80" style="width: 35px; height: 35px; border-radius: 50%; object-fit: cover;">
                    {% endif %}
                </td>
                <td style="padding: 12px; font-weight: 600; color: #1e1b4b;">{{ emp.name }}</td>
                <td style="padding: 12px;">{{ emp.username }}</td>
                <td style="padding: 12px;">{{ emp.dob }}</td>
                <td style="padding: 12px;">{{ emp.national_id }}</td>
                <td style="padding: 12px;">{{ emp.bank_account }}</td>
                <td style="padding: 12px;">{{ emp.position }}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</div>
"""

# 3. جدول ديناميكي يعرض الطلبات الحقيقية في كل خانة لـ HR Manager
HR_REQUESTS_LIST_CONTENT = """
<div class="page-card">
    <h2 style="color: #1e1b4b; margin-bottom: 15px;">Management Section: {{ path }}</h2>
    <p style="color: #475569; margin-bottom: 20px;">Review all submitted records and requests from employees.</p>
    
    {% if requests_list %}
    <table style="width: 100%; border-collapse: collapse;">
        <thead>
            <tr style="background: #f8fafc; border-bottom: 2px solid #e2e8f0;">
                <th style="padding: 12px; text-align: left; color: #475569;">Employee</th>
                <th style="padding: 12px; text-align: left; color: #475569;">Subject / Title</th>
                <th style="padding: 12px; text-align: left; color: #475569;">Details</th>
                <th style="padding: 12px; text-align: left; color: #475569;">Date</th>
            </tr>
        </thead>
        <tbody>
            {% for item in requests_list %}
            <tr style="border-bottom: 1px solid #e2e8f0;">
                <td style="padding: 12px; font-weight: 600; color: #1e1b4b;">{{ item.employee_name }}</td>
                <td style="padding: 12px; font-weight: 600; color: #4f46e5;">{{ item.title }}</td>
                <td style="padding: 12px; color: #334155;">{{ item.details }}</td>
                <td style="padding: 12px; color: #64748b; font-size: 13px;">{{ item.date_submitted }}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
    {% else %}
    <p style="margin-top: 15px; color: #64748b; font-style: italic;">No active records found yet. Submissions will appear here live when sent by employees.</p>
    {% endif %}
</div>
"""

EMPLOYEE_HOME_CONTENT = """
<div class="welcome-section" style="margin-bottom: 25px;">
    <h1 style="font-size: 26px; color: #1e1b4b; font-weight: 700;">Welcome back, {{ current_user.name }}! 👋</h1>
    <p style="font-size: 14px; color: #64748b; margin-top: 4px;">Access all employee features, update profile info, and communicate with HR.</p>
</div>

<div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px; max-width: 900px;">
    <a href="/employee/profile" style="background: white; padding: 22px; border-radius: 14px; border: 1px solid #e2e8f0; text-decoration: none; transition: 0.2s;" onmouseover="this.style.borderColor='#6366f1'" onmouseout="this.style.borderColor='#e2e8f0'">
        <div style="display: flex; justify-content: space-between; margin-bottom: 12px;">
            <div style="width: 42px; height: 42px; border-radius: 10px; background: #eef2ff; color: #4f46e5; display: flex; align-items: center; justify-content: center; font-size: 18px;"><i class="fa-solid fa-id-card"></i></div>
            <span style="color: #94a3b8;"><i class="fa-solid fa-arrow-right"></i></span>
        </div>
        <h3 style="font-size: 16px; color: #1e1b4b; font-weight: 600; margin-bottom: 4px;">My Profile & Info</h3>
        <p style="font-size: 13px; color: #64748b;">View personal details, bank info, and update photo/password.</p>
    </a>

    <a href="/employee/complaint" style="background: white; padding: 22px; border-radius: 14px; border: 1px solid #e2e8f0; text-decoration: none; transition: 0.2s;" onmouseover="this.style.borderColor='#6366f1'" onmouseout="this.style.borderColor='#e2e8f0'">
        <div style="display: flex; justify-content: space-between; margin-bottom: 12px;">
            <div style="width: 42px; height: 42px; border-radius: 10px; background: #fee2e2; color: #ef4444; display: flex; align-items: center; justify-content: center; font-size: 18px;"><i class="fa-solid fa-triangle-exclamation"></i></div>
            <span style="color: #94a3b8;"><i class="fa-solid fa-arrow-right"></i></span>
        </div>
        <h3 style="font-size: 16px; color: #1e1b4b; font-weight: 600; margin-bottom: 4px;">Submit Complaint</h3>
        <p style="font-size: 13px; color: #64748b;">Report issues or voice concerns directly to management.</p>
    </a>

    <a href="/employee/surveys" style="background: white; padding: 22px; border-radius: 14px; border: 1px solid #e2e8f0; text-decoration: none; transition: 0.2s;" onmouseover="this.style.borderColor='#6366f1'" onmouseout="this.style.borderColor='#e2e8f0'">
        <div style="display: flex; justify-content: space-between; margin-bottom: 12px;">
            <div style="width: 42px; height: 42px; border-radius: 10px; background: #eef2ff; color: #4f46e5; display: flex; align-items: center; justify-content: center; font-size: 18px;"><i class="fa-solid fa-square-poll-vertical"></i></div>
            <span style="color: #94a3b8;"><i class="fa-solid fa-arrow-right"></i></span>
        </div>
        <h3 style="font-size: 16px; color: #1e1b4b; font-weight: 600; margin-bottom: 4px;">Surveys & Feedback</h3>
        <p style="font-size: 13px; color: #64748b;">Take active company surveys and rate workplace environment.</p>
    </a>

    <a href="/employee/ask-hr" style="background: white; padding: 22px; border-radius: 14px; border: 1px solid #e2e8f0; text-decoration: none; transition: 0.2s;" onmouseover="this.style.borderColor='#6366f1'" onmouseout="this.style.borderColor='#e2e8f0'">
        <div style="display: flex; justify-content: space-between; margin-bottom: 12px;">
            <div style="width: 42px; height: 42px; border-radius: 10px; background: #eef2ff; color: #4f46e5; display: flex; align-items: center; justify-content: center; font-size: 18px;"><i class="fa-solid fa-comments"></i></div>
            <span style="color: #94a3b8;"><i class="fa-solid fa-arrow-right"></i></span>
        </div>
        <h3 style="font-size: 16px; color: #1e1b4b; font-weight: 600; margin-bottom: 4px;">Ask HR Manager</h3>
        <p style="font-size: 13px; color: #64748b;">Send direct questions or inquiries regarding policies & work.</p>
    </a>

    <a href="/employee/talents" style="background: white; padding: 22px; border-radius: 14px; border: 1px solid #e2e8f0; text-decoration: none; transition: 0.2s; grid-column: span 2;" onmouseover="this.style.borderColor='#6366f1'" onmouseout="this.style.borderColor='#e2e8f0'">
        <div style="display: flex; justify-content: space-between; margin-bottom: 12px;">
            <div style="width: 42px; height: 42px; border-radius: 10px; background: #eef2ff; color: #4f46e5; display: flex; align-items: center; justify-content: center; font-size: 18px;"><i class="fa-solid fa-graduation-cap"></i></div>
            <span style="color: #94a3b8;"><i class="fa-solid fa-arrow-right"></i></span>
        </div>
        <h3 style="font-size: 16px; color: #1e1b4b; font-weight: 600; margin-bottom: 4px;">Talent & Internships Requests</h3>
        <p style="font-size: 13px; color: #64748b;">Apply for internal skill development, workshops, or request interns.</p>
    </a>
</div>
"""

EMPLOYEE_PROFILE_CONTENT = """
<div class="page-card" style="max-width: 750px;">
    <h2 style="color: #1e1b4b; margin-bottom: 25px; display: flex; align-items: center; gap: 10px;"><i class="fa-solid fa-id-card"></i> My Personal & Professional Info</h2>
    
    {% if msg %}
    <p style="color: #10b981; font-size: 13px; margin-bottom: 20px; font-weight: 600;">{{ msg }}</p>
    {% endif %}

    <div style="display: flex; align-items: center; gap: 20px; margin-bottom: 30px; background: #f8fafc; padding: 20px; border-radius: 12px; border: 1px solid #e2e8f0;">
        {% if current_user.avatar %}
            <img src="{{ current_user.avatar }}" alt="Avatar" style="width: 80px; height: 80px; border-radius: 50%; object-fit: cover; border: 3px solid #4f46e5;">
        {% else %}
            <img src="https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=150&q=80" alt="Avatar" style="width: 80px; height: 80px; border-radius: 50%; object-fit: cover; border: 3px solid #4f46e5;">
        {% endif %}
        <div>
            <h3 style="font-size: 18px; color: #1e1b4b; font-weight: 700;">{{ current_user.name }}</h3>
            <p style="font-size: 14px; color: #4f46e5; font-weight: 600; margin-top: 2px;">{{ current_user.position }}</p>
            <p style="font-size: 12px; color: #64748b; margin-top: 4px;">Username ID: <strong>{{ current_user.username }}</strong></p>
        </div>
    </div>

    <form method="POST" enctype="multipart/form-data">
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px;">
            <div>
                <label style="display: block; font-size: 13px; font-weight: 600; color: #334155; margin-bottom: 6px;">Date of Birth</label>
                <input type="text" value="{{ current_user.dob }}" disabled style="width: 100%; padding: 12px; border: 1px solid #cbd5e1; border-radius: 8px; background: #f1f5f9; color: #64748b;">
            </div>
            <div>
                <label style="display: block; font-size: 13px; font-weight: 600; color: #334155; margin-bottom: 6px;">National ID Number</label>
                <input type="text" value="{{ current_user.national_id }}" disabled style="width: 100%; padding: 12px; border: 1px solid #cbd5e1; border-radius: 8px; background: #f1f5f9; color: #64748b;">
            </div>
        </div>

        <div style="margin-bottom: 20px;">
            <label style="display: block; font-size: 13px; font-weight: 600; color: #334155; margin-bottom: 6px;">Bank Account Number</label>
            <input type="text" value="{{ current_user.bank_account }}" disabled style="width: 100%; padding: 12px; border: 1px solid #cbd5e1; border-radius: 8px; background: #f1f5f9; color: #64748b;">
        </div>

        <hr style="border: 0; border-top: 1px solid #e2e8f0; margin: 25px 0;">

        <h3 style="font-size: 16px; color: #1e1b4b; font-weight: 600; margin-bottom: 15px;">Update Profile Settings</h3>

        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px;">
            <div>
                <label style="display: block; font-size: 13px; font-weight: 600; color: #334155; margin-bottom: 6px;">Full Name</label>
                <input type="text" name="name" value="{{ current_user.name }}" required style="width: 100%; padding: 12px; border: 1px solid #cbd5e1; border-radius: 8px; font-size: 14px;">
            </div>
            <div>
                <label style="display: block; font-size: 13px; font-weight: 600; color: #334155; margin-bottom: 6px;">New Password</label>
                <input type="password" name="password" placeholder="••••••••" style="width: 100%; padding: 12px; border: 1px solid #cbd5e1; border-radius: 8px; font-size: 14px;">
            </div>
        </div>

        <div style="margin-bottom: 25px;">
            <label style="display: block; font-size: 13px; font-weight: 600; color: #334155; margin-bottom: 6px;">Upload Profile Picture</label>
            <input type="file" name="avatar_file" accept="image/*" style="width: 100%; padding: 10px; border: 1px solid #cbd5e1; border-radius: 8px; background: #f8fafc; font-size: 14px;">
        </div>

        <button type="submit" class="btn-primary" style="width: 100%;">Save Changes</button>
    </form>
</div>
"""

EMPLOYEE_COMPLAINT_CONTENT = """
<div class="page-card" style="max-width: 650px;">
    <h2 style="color: #1e1b4b; margin-bottom: 15px;"><i class="fa-solid fa-triangle-exclamation"></i> Submit a Complaint</h2>
    <p style="color: #64748b; margin-bottom: 20px; font-size: 14px;">Submit any workplace issue or grievance confidentially to HR management.</p>
    
    {% if msg %}
    <p style="color: #10b981; font-size: 13px; margin-bottom: 15px; font-weight: 600;">{{ msg }}</p>
    {% endif %}

    <form method="POST">
        <div style="margin-bottom: 20px;">
            <label style="display: block; font-size: 13px; font-weight: 600; color: #334155; margin-bottom: 6px;">Complaint Subject</label>
            <input type="text" name="subject" required placeholder="e.g. Workplace Condition / Team Issue" style="width: 100%; padding: 12px; border: 1px solid #cbd5e1; border-radius: 8px; font-size: 14px;">
        </div>

        <div style="margin-bottom: 25px;">
            <label style="display: block; font-size: 13px; font-weight: 600; color: #334155; margin-bottom: 6px;">Detailed Explanation</label>
            <textarea name="message" rows="5" required placeholder="Describe the details of your complaint..." style="width: 100%; padding: 12px; border: 1px solid #cbd5e1; border-radius: 8px; font-size: 14px; resize: vertical;"></textarea>
        </div>

        <button type="submit" class="btn-primary" style="width: 100%;">Submit Complaint</button>
    </form>
</div>
"""

EMPLOYEE_SURVEY_CONTENT = """
<div class="page-card" style="max-width: 700px;">
    <h2 style="color: #1e1b4b; margin-bottom: 15px;"><i class="fa-solid fa-square-poll-vertical"></i> Employee Satisfaction Survey</h2>
    <p style="color: #64748b; margin-bottom: 20px; font-size: 14px;">Please take a moment to answer these questions to help us improve workplace satisfaction.</p>
    
    {% if msg %}
    <p style="color: #10b981; font-size: 13px; margin-bottom: 15px; font-weight: 600;">{{ msg }}</p>
    {% endif %}

    <form method="POST">
        <div style="margin-bottom: 20px;">
            <label style="display: block; font-size: 14px; font-weight: 600; color: #334155; margin-bottom: 8px;">1. How satisfied are you with your current work environment?</label>
            <select name="q1" style="width: 100%; padding: 12px; border: 1px solid #cbd5e1; border-radius: 8px; font-size: 14px;">
                <option>Very Satisfied</option>
                <option>Satisfied</option>
                <option>Neutral</option>
                <option>Dissatisfied</option>
            </select>
        </div>

        <div style="margin-bottom: 25px;">
            <label style="display: block; font-size: 14px; font-weight: 600; color: #334155; margin-bottom: 8px;">2. Any suggestions for improving company communication and culture?</label>
            <textarea name="q2" rows="4" required placeholder="Your feedback..." style="width: 100%; padding: 12px; border: 1px solid #cbd5e1; border-radius: 8px; font-size: 14px; resize: vertical;"></textarea>
        </div>

        <button type="submit" class="btn-primary" style="width: 100%;">Submit Survey Response</button>
    </form>
</div>
"""

EMPLOYEE_ASK_HR_CONTENT = """
<div class="page-card" style="max-width: 650px;">
    <h2 style="color: #1e1b4b; margin-bottom: 15px;"><i class="fa-solid fa-comments"></i> Ask HR Manager</h2>
    <p style="color: #64748b; margin-bottom: 20px; font-size: 14px;">Have a question about leave days, payroll, or company policy? Ask HR directly.</p>
    
    {% if msg %}
    <p style="color: #10b981; font-size: 13px; margin-bottom: 15px; font-weight: 600;">{{ msg }}</p>
    {% endif %}

    <form method="POST">
        <div style="margin-bottom: 20px;">
            <label style="display: block; font-size: 13px; font-weight: 600; color: #334155; margin-bottom: 6px;">Question Topic</label>
            <input type="text" name="topic" required placeholder="e.g. Annual Leave Request / Payslip clarification" style="width: 100%; padding: 12px; border: 1px solid #cbd5e1; border-radius: 8px; font-size: 14px;">
        </div>

        <div style="margin-bottom: 25px;">
            <label style="display: block; font-size: 13px; font-weight: 600; color: #334155; margin-bottom: 6px;">Your Question</label>
            <textarea name="question" rows="5" required placeholder="Type your question for HR..." style="width: 100%; padding: 12px; border: 1px solid #cbd5e1; border-radius: 8px; font-size: 14px; resize: vertical;"></textarea>
        </div>

        <button type="submit" class="btn-primary" style="width: 100%;">Send Question to HR</button>
    </form>
</div>
"""

EMPLOYEE_TALENT_CONTENT = """
<div class="page-card" style="max-width: 650px;">
    <h2 style="color: #1e1b4b; margin-bottom: 15px;"><i class="fa-solid fa-graduation-cap"></i> Talent & Internship Request</h2>
    <p style="color: #64748b; margin-bottom: 20px; font-size: 14px;">Request training programs, skill certifications, or request an intern for your department.</p>
    
    {% if msg %}
    <p style="color: #10b981; font-size: 13px; margin-bottom: 15px; font-weight: 600;">{{ msg }}</p>
    {% endif %}

    <form method="POST">
        <div style="margin-bottom: 20px;">
            <label style="display: block; font-size: 13px; font-weight: 600; color: #334155; margin-bottom: 6px;">Request Type</label>
            <select name="type" style="width: 100%; padding: 12px; border: 1px solid #cbd5e1; border-radius: 8px; font-size: 14px;">
                <option>Professional Training Course</option>
                <option>Skill Certification Support</option>
                <option>Request Intern Assistant</option>
                <option>Workshop / Webinar Proposal</option>
            </select>
        </div>

        <div style="margin-bottom: 25px;">
            <label style="display: block; font-size: 13px; font-weight: 600; color: #334155; margin-bottom: 6px;">Proposal / Justification Details</label>
            <textarea name="details" rows="5" required placeholder="Describe the course, training, or internship request details..." style="width: 100%; padding: 12px; border: 1px solid #cbd5e1; border-radius: 8px; font-size: 14px; resize: vertical;"></textarea>
        </div>

        <button type="submit" class="btn-primary" style="width: 100%;">Submit Request</button>
    </form>
</div>
"""


def render_page(content_html, title, active_page, is_hr=True, **context):
  user = User.query.filter_by(username=session.get("user")).first()
  if is_hr:
    full_html = BASE_LAYOUT_HR.replace("HR_CONTENT_PLACEHOLDER", content_html)
  else:
    full_html = BASE_LAYOUT_EMPLOYEE.replace(
        "EMPLOYEE_CONTENT_PLACEHOLDER", content_html
    )
  return render_template_string(
      full_html, title=title, active_page=active_page, current_user=user, **context
  )


@app.route("/")
def home():
  return render_template_string(LOGIN_TEMPLATE, step="select")


@app.route("/login-form")
def login_form():
  role = request.args.get("role", "employee")
  return render_template_string(
      LOGIN_TEMPLATE, step="form", role=role, error=None
  )


@app.route("/authenticate", methods=["POST"])
def authenticate():
  role = request.form.get("role")
  username = request.form.get("username")
  password = request.form.get("password")

  user = User.query.filter_by(
      username=username, password=password, role=role
  ).first()
  if user:
    session["user"] = user.username
    session["role"] = user.role
    session["name"] = user.name
    return redirect(
        url_for("hr_dashboard")
        if user.role == "hr"
        else url_for("employee_dashboard")
    )
  return render_template_string(
      LOGIN_TEMPLATE,
      step="form",
      role=role,
      error=f"Invalid username or password for {role.upper()} access.",
  )


# HR Routes
@app.route("/hr-dashboard")
def hr_dashboard():
  if session.get("role") != "hr":
    return redirect(url_for("home"))
  return render_page(
      HR_HOME_CONTENT, title="HR Dashboard", active_page="home", is_hr=True
  )


@app.route("/hr/profile", methods=["GET", "POST"])
def hr_profile():
  if session.get("role") != "hr":
    return redirect(url_for("home"))
  user = User.query.filter_by(username=session.get("user")).first()
  msg = None

  if request.method == "POST":
    new_name = request.form.get("name")
    new_password = request.form.get("password")
    file = request.files.get("avatar_file")

    if new_name:
      user.name = new_name
      session["name"] = new_name
    if new_password:
      user.password = new_password
    if file and file.filename != "":
      filename = secure_filename(file.filename)
      filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
      file.save(filepath)
      user.avatar = "/" + filepath.replace("\\", "/")

    db.session.commit()
    msg = "Profile updated successfully!"

  return render_page(
      PROFILE_CONTENT,
      title="Profile Settings",
      active_page="",
      msg=msg,
      is_hr=True,
  )


@app.route("/hr/add-employee", methods=["GET", "POST"])
def add_employee():
  if session.get("role") != "hr":
    return redirect(url_for("home"))
  msg = None
  if request.method == "POST":
    name = request.form.get("name")
    dob = request.form.get("dob")
    national_id = request.form.get("national_id")
    bank_account = request.form.get("bank_account")
    username = request.form.get("username")
    password = request.form.get("password")
    position = request.form.get("position")
    file = request.files.get("avatar_file")

    if User.query.filter_by(username=username).first():
      msg = "Error: Username already exists!"
    else:
      avatar_path = ""
      if file and file.filename != "":
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(filepath)
        avatar_path = "/" + filepath.replace("\\", "/")

      new_emp = User(
          username=username,
          password=password,
          role="employee",
          name=name,
          position=position,
          dob=dob,
          national_id=national_id,
          bank_account=bank_account,
          avatar=avatar_path,
      )
      db.session.add(new_emp)
      db.session.commit()
      msg = "Employee added successfully with all details!"

  return render_page(
      ADD_EMPLOYEE_CONTENT,
      title="Add New Employee",
      active_page="add",
      msg=msg,
      is_hr=True,
  )


@app.route("/hr/employees")
def all_employees():
  if session.get("role") != "hr":
    return redirect(url_for("home"))
  employees = User.query.filter_by(role="employee").all()
  return render_page(
      ALL_EMPLOYEES_CONTENT,
      title="All Employees",
      active_page="employees",
      employees=employees,
      is_hr=True,
  )


# 4. مسارات HR لعرض الجداول الحقيقية المجلوبة من قاعدة البيانات
@app.route("/hr/complaints")
def hr_complaints():
  if session.get("role") != "hr":
    return redirect(url_for("home"))
  requests_list = RequestItem.query.filter_by(category="complaint").all()
  return render_page(
      HR_REQUESTS_LIST_CONTENT,
      title="Employee Complaints",
      active_page="complaints",
      path="Complaints",
      requests_list=requests_list,
      is_hr=True,
  )


@app.route("/hr/surveys")
def hr_surveys():
  if session.get("role") != "hr":
    return redirect(url_for("home"))
  requests_list = RequestItem.query.filter_by(category="survey").all()
  return render_page(
      HR_REQUESTS_LIST_CONTENT,
      title="Employee Surveys",
      active_page="surveys",
      path="Surveys & Feedback",
      requests_list=requests_list,
      is_hr=True,
  )


@app.route("/hr/questions")
def hr_questions():
  if session.get("role") != "hr":
    return redirect(url_for("home"))
  requests_list = RequestItem.query.filter_by(category="question").all()
  return render_page(
      HR_REQUESTS_LIST_CONTENT,
      title="Employee Questions",
      active_page="questions",
      path="Questions",
      requests_list=requests_list,
      is_hr=True,
  )


@app.route("/hr/talents")
def hr_talents():
  if session.get("role") != "hr":
    return redirect(url_for("home"))
  requests_list = RequestItem.query.filter_by(category="talent").all()
  return render_page(
      HR_REQUESTS_LIST_CONTENT,
      title="Talent & Internship Requests",
      active_page="talents",
      path="Talent & Internships",
      requests_list=requests_list,
      is_hr=True,
  )


# Employee Routes
@app.route("/employee-dashboard")
def employee_dashboard():
  if session.get("role") != "employee":
    return redirect(url_for("home"))
  return render_page(
      EMPLOYEE_HOME_CONTENT,
      title="Employee Dashboard",
      active_page="home",
      is_hr=False,
  )


@app.route("/employee/profile", methods=["GET", "POST"])
def employee_profile():
  if session.get("role") != "employee":
    return redirect(url_for("home"))
  user = User.query.filter_by(username=session.get("user")).first()
  msg = None

  if request.method == "POST":
    new_name = request.form.get("name")
    new_password = request.form.get("password")
    file = request.files.get("avatar_file")

    if new_name:
      user.name = new_name
      session["name"] = new_name
    if new_password:
      user.password = new_password
    if file and file.filename != "":
      filename = secure_filename(file.filename)
      filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
      file.save(filepath)
      user.avatar = "/" + filepath.replace("\\", "/")

    db.session.commit()
    msg = "Profile updated successfully!"

  return render_page(
      EMPLOYEE_PROFILE_CONTENT,
      title="My Profile",
      active_page="profile",
      msg=msg,
      is_hr=False,
  )


# 5. حفظ كافة خانات الموظف في قاعدة البيانات عبر db.session.add(...) و db.session.commit()
@app.route("/employee/complaint", methods=["GET", "POST"])
def employee_complaint():
  if session.get("role") != "employee":
    return redirect(url_for("home"))
  msg = None
  if request.method == "POST":
    subject = request.form.get("subject")
    message = request.form.get("message")
    new_req = RequestItem(
        category="complaint",
        employee_name=session.get("name"),
        title=subject,
        details=message,
        date_submitted=datetime.now().strftime("%Y-%m-%d %H:%M"),
    )
    db.session.add(new_req)
    db.session.commit()
    msg = "Your complaint has been submitted to HR successfully!"

  return render_page(
      EMPLOYEE_COMPLAINT_CONTENT,
      title="Submit Complaint",
      active_page="complaint",
      msg=msg,
      is_hr=False,
  )


@app.route("/employee/surveys", methods=["GET", "POST"])
def employee_surveys():
  if session.get("role") != "employee":
    return redirect(url_for("home"))
  msg = None
  if request.method == "POST":
    q1 = request.form.get("q1")
    q2 = request.form.get("q2")
    details = f"Satisfaction Level: {q1} | Feedback: {q2}"
    new_req = RequestItem(
        category="survey",
        employee_name=session.get("name"),
        title="Satisfaction Survey Response",
        details=details,
        date_submitted=datetime.now().strftime("%Y-%m-%d %H:%M"),
    )
    db.session.add(new_req)
    db.session.commit()
    msg = "Thank you! Your survey responses have been submitted."

  return render_page(
      EMPLOYEE_SURVEY_CONTENT,
      title="Surveys & Feedback",
      active_page="surveys",
      msg=msg,
      is_hr=False,
  )


@app.route("/employee/ask-hr", methods=["GET", "POST"])
def employee_ask_hr():
  if session.get("role") != "employee":
    return redirect(url_for("home"))
  msg = None
  if request.method == "POST":
    topic = request.form.get("topic")
    question = request.form.get("question")
    new_req = RequestItem(
        category="question",
        employee_name=session.get("name"),
        title=topic,
        details=question,
        date_submitted=datetime.now().strftime("%Y-%m-%d %H:%M"),
    )
    db.session.add(new_req)
    db.session.commit()
    msg = "Your question has been sent to the HR Manager!"

  return render_page(
      EMPLOYEE_ASK_HR_CONTENT,
      title="Ask HR Manager",
      active_page="ask-hr",
      msg=msg,
      is_hr=False,
  )


@app.route("/employee/talents", methods=["GET", "POST"])
def employee_talents():
  if session.get("role") != "employee":
    return redirect(url_for("home"))
  msg = None
  if request.method == "POST":
    req_type = request.form.get("type")
    details = request.form.get("details")
    new_req = RequestItem(
        category="talent",
        employee_name=session.get("name"),
        title=req_type,
        details=details,
        date_submitted=datetime.now().strftime("%Y-%m-%d %H:%M"),
    )
    db.session.add(new_req)
    db.session.commit()
    msg = "Your Talent & Internship request has been submitted successfully!"

  return render_page(
      EMPLOYEE_TALENT_CONTENT,
      title="Talent & Internships",
      active_page="talents",
      msg=msg,
      is_hr=False,
  )


@app.route("/logout")
def logout():
  session.clear()
  return redirect(url_for("home"))


if __name__ == "__main__":
  port = int(os.environ.get("PORT", 5000))
  app.run(host="0.0.0.0", port=port)