

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session
)

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from dotenv import load_dotenv
import os

from extensions import db


# =========================================================
# LOAD ENVIRONMENT VARIABLES
# =========================================================

load_dotenv()


# =========================================================
# CREATE FLASK APP
# =========================================================

app = Flask(__name__)


# =========================================================
# DATABASE CONFIGURATION
# =========================================================

app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
    "DATABASE_URL"
)

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False


# =========================================================
# SECRET KEY
# =========================================================

app.secret_key = os.environ.get("SECRET_KEY")

# =========================================================
# INITIALIZE DATABASE
# =========================================================

db.init_app(app)


# =========================================================
# IMPORT MODELS
# =========================================================

from models.student import Student
from models.course import Course
from models.enrollment import Enrollment
from models.certification_exam import CertificationExam

# =========================================================
# HOME PAGE
# =========================================================

@app.route("/")
def home():

    return "Course Registration System is running!"


# =========================================================
# STUDENT REGISTRATION
# =========================================================

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form["name"]

        email = request.form["email"]

        password = request.form["password"]

        department = request.form["department"]

        year = request.form["year"]


        # -------------------------------------------------
        # Check whether email already exists
        # -------------------------------------------------

        existing_student = Student.query.filter_by(
            email=email
        ).first()


        if existing_student:

            return "Email already registered!"


        # -------------------------------------------------
        # Hash password before storing
        # -------------------------------------------------

        hashed_password = generate_password_hash(
            password
        )


        # -------------------------------------------------
        # Create new student
        # -------------------------------------------------

        student = Student(

            name=name,

            email=email,

            password=hashed_password,

            department=department,

            year=year

        )


        # -------------------------------------------------
        # Save student to database
        # -------------------------------------------------

        db.session.add(student)

        db.session.commit()


        # -------------------------------------------------
        # Redirect to login
        # -------------------------------------------------

        return redirect(
            url_for("login")
        )


    return render_template(
        "register.html"
    )


# =========================================================
# STUDENT LOGIN
# =========================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]

        password = request.form["password"]


        # -------------------------------------------------
        # Find student using email
        # -------------------------------------------------

        student = Student.query.filter_by(
            email=email
        ).first()


        # -------------------------------------------------
        # Check password using stored hash
        # -------------------------------------------------

        if student and check_password_hash(
            student.password,
            password
        ):

            session["student_id"] = student.student_id

            session["student_name"] = student.name


            return redirect(
                url_for("dashboard")
            )


        return "Invalid email or password!"


    return render_template(
        "login.html"
    )


# =========================================================
# STUDENT DASHBOARD
# =========================================================

@app.route("/dashboard")
def dashboard():

    # Check whether student is logged in

    if "student_id" not in session:

        return redirect(
            url_for("login")
        )


    return render_template(

        "dashboard.html",

        student_name=session["student_name"]

    )


# =========================================================
# AVAILABLE COURSES
# =========================================================

@app.route("/courses")
def courses():

    # Check login

    if "student_id" not in session:

        return redirect(
            url_for("login")
        )


    # Get all courses

    all_courses = Course.query.all()


    # Store course information

    course_data = []


    for course in all_courses:

        # Count registered students

        registered_count = Enrollment.query.filter_by(

            course_id=course.course_id

        ).count()


        # Calculate available seats

        available_seats = (
            course.capacity - registered_count
        )


        # Prevent negative seats

        if available_seats < 0:

            available_seats = 0


        course_data.append({

            "course": course,

            "registered_count": registered_count,

            "available_seats": available_seats

        })


    return render_template(

        "courses.html",

        course_data=course_data

    )


# =========================================================
# REGISTER FOR A COURSE
# =========================================================

@app.route("/register-course/<int:course_id>")
def register_course(course_id):

    # Check login

    if "student_id" not in session:

        return redirect(
            url_for("login")
        )


    # Get logged-in student's ID

    student_id = session["student_id"]


    # Find course

    course = Course.query.get(course_id)


    # Check whether course exists

    if not course:

        return "Course not found!"


    # -------------------------------------------------
    # Check duplicate registration
    # -------------------------------------------------

    existing_enrollment = Enrollment.query.filter_by(

        student_id=student_id,

        course_id=course_id

    ).first()


    if existing_enrollment:

        return "You are already registered for this course!"


    # -------------------------------------------------
    # Count registered students
    # -------------------------------------------------

    registered_count = Enrollment.query.filter_by(

        course_id=course_id

    ).count()


    # -------------------------------------------------
    # Check course capacity
    # -------------------------------------------------

    if registered_count >= course.capacity:

        return "Sorry, this course is full!"


    # -------------------------------------------------
    # Create enrollment
    # -------------------------------------------------

    enrollment = Enrollment(

        student_id=student_id,

        course_id=course_id

    )


    # Save enrollment

    db.session.add(enrollment)

    db.session.commit()


    # Return to courses

    return redirect(
        url_for("courses")
    )


# =========================================================
# MY COURSES
# =========================================================

@app.route("/my-courses")
def my_courses():

    if "student_id" not in session:
        return redirect(url_for("login"))

    student_id = session["student_id"]

    enrollments = Enrollment.query.filter_by(
        student_id=student_id
    ).all()

    exam_registrations = CertificationExam.query.filter_by(
        student_id=student_id
    ).all()

    registered_exam_course_ids = {
    exam.course_id
    for exam in CertificationExam.query.filter_by(
        student_id=session["student_id"]
    ).all()
    if exam.payment_status == "Paid"
}

    return render_template(
    "my_courses.html",
    enrollments=enrollments,
    registered_exam_course_ids=registered_exam_course_ids
)
# =========================================================
# CERTIFICATION EXAM REGISTRATION
# =========================================================

@app.route("/register-exam/<int:course_id>")
def register_exam(course_id):

    if "student_id" not in session:
        return redirect(url_for("login"))

    student_id = session["student_id"]

    # Check whether student is registered for this course
    enrollment = Enrollment.query.filter_by(
        student_id=student_id,
        course_id=course_id
    ).first()

    if not enrollment:
        return "You must register for the course first!"

    course = Course.query.get(course_id)

    if not course:
        return "Course not found!"

    # Check whether exam registration already exists
    existing_exam = CertificationExam.query.filter_by(
        student_id=student_id,
        course_id=course_id
    ).first()

    if existing_exam:
        return render_template(
            "exam_payment.html",
            course=course,
            exam=existing_exam
        )

    # Certification exam fee
    exam_fee = 100

    return render_template(
        "exam_payment.html",
        course=course,
        exam=None,
        exam_fee=exam_fee
    )





@app.route(
    "/confirm-exam-payment/<int:course_id>",
    methods=["POST"]
)
def confirm_exam_payment(course_id):

    if "student_id" not in session:
        return redirect(url_for("login"))

    student_id = session["student_id"]

    # Find the course
    course = Course.query.get(course_id)

    if not course:
        return "Course not found!"

    # Check whether student is registered for this course
    enrollment = Enrollment.query.filter_by(
        student_id=student_id,
        course_id=course_id
    ).first()

    if not enrollment:
        return "You must register for the course first!"

    # Check existing exam registration
    existing_exam = CertificationExam.query.filter_by(
        student_id=student_id,
        course_id=course_id
    ).first()

    # If already registered and paid
    if existing_exam:

        if existing_exam.payment_status == "Paid":

            return redirect(
                url_for(
                    "exam_success",
                    exam_id=existing_exam.exam_id
                )
            )

        # If record exists but payment was pending,
        # mark it as paid
        existing_exam.payment_status = "Paid"
        existing_exam.registration_status = "Registered"

        db.session.commit()

        return redirect(
            url_for(
                "exam_success",
                exam_id=existing_exam.exam_id
            )
        )

    # Create a new exam registration
    exam = CertificationExam(
        student_id=student_id,
        course_id=course_id,
        exam_fee=100,
        payment_status="Paid",
        registration_status="Registered"
    )

    db.session.add(exam)
    db.session.commit()

    return redirect(
        url_for(
            "exam_success",
            exam_id=exam.exam_id
        )
    )

@app.route("/exam-success/<int:exam_id>")
def exam_success(exam_id):

    if "student_id" not in session:
        return redirect(url_for("login"))

    exam = CertificationExam.query.get(exam_id)

    if not exam:
        return "Exam registration not found!"

    return render_template(
        "exam_success.html",
        exam=exam
    )

# =========================================================
# DROP COURSE
# =========================================================

@app.route("/drop-course/<int:course_id>")
def drop_course(course_id):

    # Check login

    if "student_id" not in session:

        return redirect(
            url_for("login")
        )


    # Get logged-in student's ID

    student_id = session["student_id"]


    # Find enrollment

    enrollment = Enrollment.query.filter_by(

        student_id=student_id,

        course_id=course_id

    ).first()


    # Check enrollment

    if not enrollment:

        return "You are not registered for this course!"


    # Delete enrollment

    db.session.delete(enrollment)

    db.session.commit()


    # Return to My Courses

    return redirect(
        url_for("my_courses")
    )


# =========================================================
# MY PROFILE
# =========================================================

@app.route("/profile")
def profile():

    # Check login

    if "student_id" not in session:

        return redirect(
            url_for("login")
        )


    # Get logged-in student's ID

    student_id = session["student_id"]


    # Find student

    student = Student.query.get(student_id)


    # Check student

    if not student:

        return "Student not found!"


    # Count registered courses

    registered_courses = Enrollment.query.filter_by(

        student_id=student_id

    ).count()


    return render_template(

        "profile.html",

        student=student,

        registered_courses=registered_courses

    )


# =========================================================
# EDIT PROFILE
# =========================================================

@app.route("/edit-profile", methods=["GET", "POST"])
def edit_profile():

    # Check login

    if "student_id" not in session:

        return redirect(
            url_for("login")
        )


    # Get logged-in student's ID

    student_id = session["student_id"]


    # Get student

    student = Student.query.get(student_id)


    # Check student

    if not student:

        return "Student not found!"


    # -------------------------------------------------
    # When form is submitted
    # -------------------------------------------------

    if request.method == "POST":

        name = request.form["name"]

        department = request.form["department"]

        year = request.form["year"]


        # Update student information

        student.name = name

        student.department = department

        student.year = year


        # Update session name

        session["student_name"] = name


        # Save changes

        db.session.commit()


        # Return to profile

        return redirect(
            url_for("profile")
        )


    # Show edit form

    return render_template(

        "edit_profile.html",

        student=student

    )


# =========================================================
# LOGOUT
# =========================================================

@app.route("/logout")
def logout():

    # Clear session

    session.clear()


    # Return to login

    return redirect(
        url_for("login")
    )


# =========================================================
# RUN APPLICATION
# =========================================================

if __name__ == "__main__":

    app.run(
        debug=True
    )