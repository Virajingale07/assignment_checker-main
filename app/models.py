from app import db
from datetime import datetime


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(10), nullable=False)  # 'student', 'teacher', 'admin'
     # New fields for Email Verification
    email = db.Column(db.String(120), unique=True, nullable=False)  # Now required
    is_verified = db.Column(db.Boolean, default=False)  # Access Gatekeeper
    otp_code = db.Column(db.String(6), nullable=True)  # Temporary 6-digit code
    otp_expiry = db.Column(db.DateTime, nullable=True)  # Code expiration

    # Student Fields
    roll_no = db.Column(db.String(20))
    class_name = db.Column(db.String(50))
    division = db.Column(db.String(10))

    # Teacher Fields
    assigned_classes = db.Column(db.JSON, nullable=True, default=list)
    email = db.Column(db.String(120))
    subject = db.Column(db.String(100))
    bio = db.Column(db.Text)

    # Forgot Password Fields
    reset_token = db.Column(db.String(100), nullable=True)

    assignments = db.relationship('Assignment', backref='teacher', lazy=True)
    submissions = db.relationship('Submission', backref='student', lazy=True)


class Assignment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    class_name = db.Column(db.String(50), nullable=False)
    division = db.Column(db.String(10), nullable=False)
    subject_name = db.Column(db.String(100), nullable=False)
    teacher_name = db.Column(db.String(100), nullable=False)
    answer_key_content = db.Column(db.Text, nullable=True)
    questionnaire_file = db.Column(db.LargeBinary, nullable=True)
    questionnaire_filename = db.Column(db.String(100))
    teacher_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    submissions = db.relationship('Submission', backref='assignment', lazy=True, cascade="all, delete-orphan")


class Submission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    assignment_id = db.Column(db.Integer, db.ForeignKey('assignment.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    submitted_file = db.Column(db.LargeBinary, nullable=True)
    submission_date = db.Column(db.DateTime, default=datetime.utcnow)
    score = db.Column(db.Float, default=0.0)
    detailed_feedback = db.Column(db.JSON, nullable=True)


class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)

    # New Field for Lecture-Wise Attendance
    lecture_subject = db.Column(db.String(100), nullable=False, default="General")

    status = db.Column(db.String(10), nullable=False)  # 'Present', 'Absent'
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    class_name = db.Column(db.String(50))
    division = db.Column(db.String(10))

class Test(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    subject = db.Column(db.String(100))
    class_name = db.Column(db.String(50))
    division = db.Column(db.String(10))
    duration = db.Column(db.Integer) # in minutes
    questions_json = db.Column(db.JSON, nullable=False) # Stores the final edited MCQs
    teacher_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class TestResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    test_id = db.Column(db.Integer, db.ForeignKey('test.id'))
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    score = db.Column(db.Integer)
    total_questions = db.Column(db.Integer)
    completed_at = db.Column(db.DateTime, default=datetime.utcnow)