from flask import Blueprint, render_template, request, redirect, session, flash, url_for, send_file
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from sqlalchemy.orm.attributes import flag_modified
from sqlalchemy.sql import func
from io import BytesIO
import pypdf
from pdf2image import convert_from_bytes
import uuid
from datetime import datetime
from functools import wraps

# --- IMPORTS ---
from app.models import db, User, Assignment, Submission, Attendance
from app.ai_evaluator import compute_score, generate_answer_key, extract_text_from_image

routes = Blueprint('routes', __name__)


# --- RBAC DECORATOR ---
def role_required(role):
    """
    Middleware to ensure the user is logged in and possesses the correct role.
    """

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                flash("Please log in to access this page.", "danger")
                return redirect('/login')

            if session.get('role') != role:
                flash(f"Access Denied: You do not have {role} permissions.", "danger")
                # Redirect user to their appropriate home based on their actual role
                return redirect(url_for(f'routes.{session.get("role")}_dashboard'))
            return f(*args, **kwargs)

        return decorated_function

    return decorator


# --- HELPER: Extract Text ---
def extract_text_from_file(file_storage):
    filename = file_storage.filename.lower()
    if filename.endswith('.pdf'):
        try:
            pdf_reader = pypdf.PdfReader(file_storage)
            text = ""
            for page in pdf_reader.pages:
                extracted = page.extract_text()
                if extracted: text += extracted + "\n"
            if len(text.strip()) < 10:
                file_storage.seek(0)
                images = convert_from_bytes(file_storage.read())
                for img in images:
                    img_byte_arr = BytesIO()
                    img.save(img_byte_arr, format='JPEG')
                    text += extract_text_from_image(img_byte_arr.getvalue()) + "\n"
            file_storage.seek(0)
            return text
        except:
            return ""
    elif filename.endswith(('.png', '.jpg', '.jpeg')):
        try:
            file_bytes = file_storage.read()
            text = extract_text_from_image(file_bytes)
            file_storage.seek(0)
            return text
        except:
            return ""
    else:
        try:
            return file_storage.read().decode('utf-8', errors='ignore')
        except:
            return ""


# --- AUTH ROUTES ---
@routes.route('/')
def home():
    return redirect('/login')


@routes.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password_hash, password):
            # NEW: Check if email is verified
            if not user.is_verified:
                session['pending_verification_user_id'] = user.id
                flash("Please verify your email first.", "warning")
                return redirect('/verify-email')

        if username == 'admin' and password == 'admin123':
            admin = User.query.filter_by(username='admin').first()
            if not admin:
                admin = User(username='admin', password_hash=generate_password_hash('admin123'), role='admin')
                db.session.add(admin)
                db.session.commit()
            session['user_id'] = admin.id
            session['role'] = 'admin'
            return redirect('/admin/dashboard')

        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            session['role'] = user.role
            session['username'] = user.username

            if user.role == 'admin': return redirect('/admin/dashboard')
            if user.role == 'teacher': return redirect('/teacher/dashboard')
            return redirect('/student/dashboard')

        flash('Invalid credentials', 'danger')
    return render_template('login.html')


@routes.route('/logout')
def logout():
    session.clear()
    return redirect('/login')


import random
from datetime import datetime, timedelta


@routes.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        username = request.form.get('username')

        # Check if email or username already exists
        if User.query.filter_by(email=email).first() or User.query.filter_by(username=username).first():
            flash('Username or Email already registered.', 'danger')
            return redirect('/register')

        # 1. Generate 6-digit OTP
        otp = str(random.randint(100000, 999999))

        # 2. Create unverified user
        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(request.form.get('password')),
            role=request.form.get('role'),
            is_verified=False,  # User is locked until verified
            otp_code=otp,
            otp_expiry=datetime.utcnow() + timedelta(minutes=10)  # 10-minute window
        )

        db.session.add(user)
        db.session.commit()
        
        if send_verification_email(user.email, otp):
            session['pending_verification_user_id'] = user.id
            flash(f"Verification code sent to {user.email}.", "info")
            return redirect('/verify-email')
        else:
            # If this fails, the error in your screenshot appears
            flash("Error sending email. Please check your address.", "danger")
            return redirect('/verify-email')
        # Store user ID in session temporarily for the verification page
        session['pending_verification_user_id'] = user.id
        # Temporary bypass for testing UI logic
        send_verification_email(user.email, otp)
        flash(f"DEMO MODE: OTP is {otp}", "info")  # Still flash it so you can see it
        return redirect('/verify-email')

    return render_template('register.html')


from flask_mail import Message
from app import mail


def send_verification_email(user_email, otp):
    """
    Creates and sends the verification email via SMTP.
    """
    msg = Message('Verify Your EduAI Account',
                  recipients=[user_email])
    msg.body = f'Your 6-digit verification code is: {otp}. It will expire in 10 minutes.'

    try:
        mail.send(msg)
        return True
    except Exception as e:
        print(f"SMTP Error: {e}")  # This will show in your terminal
        return False

@routes.route('/verify-email', methods=['GET', 'POST'])
def verify_email():
    user_id = session.get('pending_verification_user_id')
    if not user_id:
        return redirect('/register')

    user = User.query.get(user_id)
    if request.method == 'POST':
        entered_otp = request.form.get('otp')

        # Check if OTP matches and is not expired
        if user.otp_code == entered_otp and datetime.utcnow() < user.otp_expiry:
            user.is_verified = True  # Unlock account
            user.otp_code = None  # Clear code
            db.session.commit()

            session.pop('pending_verification_user_id')  # Clean up session
            flash("Email verified! You can now log in.", "success")
            return redirect('/login')
        else:
            flash("Invalid or expired OTP. Please try again.", "danger")

    return render_template('verify_email.html', email=user.email)


@routes.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        username = request.form.get('username')
        user = User.query.filter_by(username=username).first()
        if user:
            token = str(uuid.uuid4())
            user.reset_token = token
            db.session.commit()
            reset_link = url_for('routes.reset_password', token=token, _external=True)
            flash(f"DEMO MODE: Password Reset Link: {reset_link}", "info")
        else:
            flash("User not found.", "danger")
    return render_template('forgot_password.html')


@routes.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    user = User.query.filter_by(reset_token=token).first()
    if not user:
        flash("Invalid token.", "danger")
        return redirect('/login')
    if request.method == 'POST':
        new_pass = request.form.get('password')
        user.password_hash = generate_password_hash(new_pass)
        user.reset_token = None
        db.session.commit()
        flash("Password reset successful!", "success")
        return redirect('/login')
    return render_template('reset_password.html')


# --- ADMIN "GOD MODE" ROUTES ---

@routes.route('/admin/dashboard')
@role_required('admin')
def admin_dashboard():
    users = User.query.order_by(User.id.desc()).all()
    assignments = Assignment.query.order_by(Assignment.id.desc()).all()
    class_map = {}

    for u in users:
        if u.role == 'student' and u.class_name and u.division:
            key = f"{u.class_name} - {u.division}"
            if key not in class_map: class_map[key] = {"students": [], "teachers": []}
            class_map[key]["students"].append(u)

        if u.role == 'teacher' and u.assigned_classes:
            for cls in u.assigned_classes:
                key = f"{cls['class_name']} - {cls['division']}"
                if key not in class_map: class_map[key] = {"students": [], "teachers": []}
                if u not in class_map[key]["teachers"]:
                    class_map[key]["teachers"].append(u)

    total_users = len(users)
    total_assignments = len(assignments)
    total_submissions = Submission.query.count()
    avg_score = db.session.query(func.avg(Submission.score)).scalar() or 0

    return render_template('admin_dashboard.html',
                           users=users,
                           assignments=assignments,
                           class_map=class_map,
                           stats={
                               "users": total_users,
                               "assignments": total_assignments,
                               "submissions": total_submissions,
                               "avg_score": round(avg_score, 1)
                           })


@routes.route('/admin/create-user', methods=['POST'])
@role_required('admin')
def admin_create_user():
    username = request.form.get('username')
    password = request.form.get('password')
    role = request.form.get('role')

    if User.query.filter_by(username=username).first():
        flash(f"Username '{username}' already exists.", "danger")
        return redirect('/admin/dashboard')

    assigned_classes = []
    class_name = request.form.get('class_name')
    division = request.form.get('division')

    if role == 'teacher' and class_name:
        assigned_classes.append({
            "class_name": class_name.strip().upper(),
            "division": division.strip().upper()
        })

    student_class = class_name.strip().upper() if role == 'student' and class_name else None
    student_div = division.strip().upper() if role == 'student' and division else None

    new_user = User(
        username=username,
        password_hash=generate_password_hash(password),
        role=role,
        class_name=student_class,
        division=student_div,
        assigned_classes=assigned_classes
    )

    db.session.add(new_user)
    db.session.commit()
    flash(f"User {username} created successfully!", "success")
    return redirect('/admin/dashboard')


@routes.route('/admin/delete-user/<int:id>', methods=['POST'])
@role_required('admin')
def delete_user(id):
    user = User.query.get_or_404(id)
    if user.id == session['user_id']:
        flash("You cannot delete the Super Admin.", "danger")
        return redirect('/admin/dashboard')
    db.session.delete(user)
    db.session.commit()
    flash(f"User {user.username} deleted.", "success")
    return redirect('/admin/dashboard')


@routes.route('/admin/edit-user/<int:id>', methods=['POST'])
@role_required('admin')
def edit_user(id):
    user = User.query.get_or_404(id)
    user.username = request.form.get('username')
    user.class_name = request.form.get('class_name')
    user.division = request.form.get('division')
    new_pass = request.form.get('new_password')
    if new_pass:
        user.password_hash = generate_password_hash(new_pass)
        flash(f"Password for {user.username} reset.", "info")
    db.session.commit()
    flash("User updated successfully.", "success")
    return redirect('/admin/dashboard')


@routes.route('/admin/delete-assignment/<int:id>', methods=['POST'])
@role_required('admin')
def admin_delete_assignment(id):
    assign = Assignment.query.get_or_404(id)
    db.session.delete(assign)
    db.session.commit()
    flash("Assignment force-deleted.", "success")
    return redirect('/admin/dashboard')


# --- TEACHER ROUTES ---
@routes.route('/teacher/dashboard')
@role_required('teacher')
def teacher_dashboard():
    teacher = User.query.get(session['user_id'])
    return render_template('teacher_dashboard.html', teacher=teacher)


@routes.route('/teacher/update-profile', methods=['POST'])
@role_required('teacher')
def update_teacher_profile():
    teacher = User.query.get(session['user_id'])
    teacher.email = request.form.get('email')
    teacher.subject = request.form.get('subject')
    teacher.bio = request.form.get('bio')
    new_class = request.form.get('new_class_name')
    new_div = request.form.get('new_division')
    if new_class and new_div:
        cls_obj = {"class_name": new_class.strip().upper(), "division": new_div.strip().upper()}
        if teacher.assigned_classes is None: teacher.assigned_classes = []
        current_list = list(teacher.assigned_classes)
        current_list.append(cls_obj)
        teacher.assigned_classes = current_list
        flag_modified(teacher, "assigned_classes")
    db.session.commit()
    return redirect('/teacher/dashboard')


@routes.route('/teacher/create-assignment', methods=['GET', 'POST'])
@role_required('teacher')
def create_assignment():
    teacher = User.query.get(session['user_id'])
    if request.method == 'POST':
        try:
            file = request.files.get('questionnaire_file')
            key_text = request.form.get('ai_generated_key')
            new_assign = Assignment(
                title=request.form.get('title'),
                class_name=request.form.get('class_name').strip().upper(),
                division=request.form.get('division').strip().upper(),
                subject_name=request.form.get('subject_name'),
                teacher_name=teacher.username,
                teacher_id=teacher.id,
                answer_key_content=key_text,
                questionnaire_file=file.read() if file else None,
                questionnaire_filename=secure_filename(file.filename) if file else "unknown.txt"
            )
            db.session.add(new_assign)
            db.session.commit()
            flash("Assignment Created!", "success")
            return redirect('/teacher/assignments')
        except Exception as e:
            flash(f"Error: {e}", "danger")
    return render_template('create_assignment.html')


@routes.route('/teacher/generate-key', methods=['POST'])
@role_required('teacher')
def generate_key_api():
    file = request.files.get('file')
    if not file: return {"error": "No file"}, 400
    text = extract_text_from_file(file)
    return {"key": generate_answer_key(text)}


@routes.route('/teacher/assignments')
@role_required('teacher')
def view_assignments():
    assignments = Assignment.query.filter_by(teacher_id=session['user_id']).all()
    return render_template('view_assignments.html', assignments=assignments)


@routes.route('/teacher/assignments/<int:id>/edit', methods=['GET', 'POST'])
@role_required('teacher')
def edit_assignment(id):
    assignment = Assignment.query.get_or_404(id)
    if request.method == 'POST':
        assignment.title = request.form.get('title')
        assignment.class_name = request.form.get('class_name')
        assignment.division = request.form.get('division')
        assignment.subject_name = request.form.get('subject_name')
        db.session.commit()
        flash("Updated!", "success")
        return redirect('/teacher/assignments')
    return render_template('edit_assignment.html', assignment=assignment)


@routes.route('/teacher/assignments/<int:id>/submissions')
@role_required('teacher')
def view_submissions(id):
    assignment = Assignment.query.get_or_404(id)
    submissions = Submission.query.filter_by(assignment_id=id).all()
    return render_template('view_submissions.html', assignment=assignment, submissions=submissions)


@routes.route('/teacher/delete-assignment/<int:id>', methods=['POST'])
@role_required('teacher')
def delete_assignment(id):
    assign = Assignment.query.get_or_404(id)
    if assign.teacher_id == session['user_id']:
        db.session.delete(assign)
        db.session.commit()
    return redirect('/teacher/assignments')


@routes.route('/teacher/attendance', methods=['GET', 'POST'])
@role_required('teacher')
def teacher_attendance():
    teacher = User.query.get(session['user_id'])
    cls = request.args.get('class_name')
    div = request.args.get('div')
    students = []
    if cls and div:
        students = User.query.filter_by(role='student', class_name=cls, division=div).all()
    if request.method == 'POST':
        date_str = request.form.get('date')
        subject_name = request.form.get('subject')
        if not date_str or not subject_name:
            flash("Error: Date and Subject required.", "danger")
            return redirect(f"/teacher/attendance?class_name={cls}&div={div}")
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
        for student in students:
            status = request.form.get(f"status_{student.id}")
            if status:
                rec = Attendance(date=date, lecture_subject=subject_name, status=status, student_id=student.id,
                                 teacher_id=teacher.id, class_name=cls, division=div)
                db.session.add(rec)
        db.session.commit()
        flash(f"Attendance for {subject_name} Saved!", "success")
        return redirect(f"/teacher/attendance?class_name={cls}&div={div}")
    return render_template('teacher_attendance.html', teacher=teacher, students=students, selected_class=cls,
                           selected_div=div, now=datetime.now())


# --- STUDENT ROUTES ---
@routes.route('/student/dashboard', methods=['GET', 'POST'])
@role_required('student')
def student_dashboard():
    student = User.query.get(session['user_id'])
    if request.method == 'POST':
        aid = request.form.get('assignment_id')
        file = request.files.get('student_answer')
        assign = Assignment.query.get(aid)
        student_text = extract_text_from_file(file)
        score, feedback = compute_score(student_text, assign.answer_key_content)
        sub = Submission(assignment_id=aid, student_id=student.id, submitted_file=file.read(), score=score,
                         detailed_feedback=feedback)
        db.session.add(sub)
        db.session.commit()
        flash(f"Graded: {score}%", "success")
        return redirect('/student/dashboard')
    assigns = Assignment.query.filter_by(class_name=student.class_name, division=student.division).all()
    my_subs = {s.assignment_id: s for s in Submission.query.filter_by(student_id=student.id).all()}
    total = Attendance.query.filter_by(student_id=student.id).count()
    present = Attendance.query.filter_by(student_id=student.id, status='Present').count()
    pct = int((present / total) * 100) if total > 0 else 0
    return render_template('student_dashboard.html', student=student, assignments=assigns, submitted_map=my_subs,
                           att_pct=pct, present_days=present, total_days=total)


@routes.route('/student/download/<int:id>')
@role_required('student')
def download_q(id):
    assign = Assignment.query.get_or_404(id)
    return send_file(BytesIO(assign.questionnaire_file), download_name=assign.questionnaire_filename,
                     as_attachment=True)


# --- PUBLIC/GENERAL API ---
@routes.route('/api/chat', methods=['POST'])
def chat_api():
    # Minor update: Added a session check for chat security
    if 'user_id' not in session: return {"response": "Unauthorized."}, 401

    data = request.json
    user_message = data.get('message', '')
    if not user_message: return {"response": "I didn't hear anything!"}
    from app.ai_evaluator import get_groq_client
    client = get_groq_client()
    if not client: return {"response": "Error: AI Brain is offline."}
    try:
        completion = client.chat.completions.create(
            messages=[{"role": "system", "content": "You are a helpful teaching assistant."},
                      {"role": "user", "content": user_message}],
            model="llama-3.3-70b-versatile",
        )
        return {"response": completion.choices[0].message.content}
    except Exception as e:
        return {"response": "Thinking error."}