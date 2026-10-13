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

from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from sqlalchemy.exc import SQLAlchemyError

from extensions import db

import os


# =========================================================
# CONFIGURATION
# =========================================================

load_dotenv()

app = Flask(__name__)

app.config["UPLOAD_FOLDER"] = os.path.join(
    app.root_path, "static", "books"
)

app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
    "DATABASE_URL"
)

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

app.secret_key = os.environ.get("SECRET_KEY")

if not app.secret_key:
    raise RuntimeError(
        "SECRET_KEY is missing from your .env file."
    )

if not app.config["SQLALCHEMY_DATABASE_URI"]:
    raise RuntimeError(
        "DATABASE_URL is missing from your .env file."
    )

ALLOWED_EXTENSIONS = {"pdf"}

db.init_app(app)


# =========================================================
# DATABASE MODELS
# =========================================================

from models.student import Student
from models.course import Course
from models.book import Book
from models.enrollment import Enrollment
from models.certification_exam import CertificationExam
from models.external_course import ExternalCourse
from models.announcement import Announcement


# =========================================================
# HELPER FUNCTIONS
# =========================================================

def allowed_file(filename):
    return (
        bool(filename)
        and "." in filename
        and filename.rsplit(".", 1)[1].lower()
        in ALLOWED_EXTENSIONS
    )


def login_required():
    return "student_id" in session


def admin_required():
    return (
        login_required()
        and session.get("role") == "admin"
    )


def get_current_student():
    if not login_required():
        return None

    return db.session.get(
        Student,
        session["student_id"]
    )


# =========================================================
# HOME
# =========================================================

@app.route("/")
def home():

    if not login_required():
        return redirect(url_for("login"))

    if session.get("role") == "admin":
        return redirect(url_for("admin_dashboard"))

    return redirect(url_for("dashboard"))


# =========================================================
# STUDENT REGISTRATION
# =========================================================

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        department = request.form.get(
            "department", ""
        ).strip()
        year = request.form.get("year", "").strip()

        if not all([
            name,
            email,
            password,
            department,
            year
        ]):
            return "Please fill in all fields.", 400

        existing_student = Student.query.filter_by(
            email=email
        ).first()

        if existing_student:
            return "Email already registered!", 409

        student = Student(
            name=name,
            email=email,
            password=generate_password_hash(password),
            department=department,
            year=year
        )

        try:
            db.session.add(student)
            db.session.commit()

        except SQLAlchemyError:
            db.session.rollback()
            app.logger.exception(
                "Student registration failed."
            )
            return "Could not register student.", 500

        return redirect(url_for("login"))

    return render_template("register.html")


# =========================================================
# LOGIN
# =========================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        student = Student.query.filter_by(
            email=email
        ).first()

        if student and check_password_hash(
            student.password, password
        ):

            session.clear()

            session["student_id"] = student.student_id
            session["role"] = student.role
            session["student_name"] = student.name

            if student.role == "admin":
                return redirect(
                    url_for("admin_dashboard")
                )

            return redirect(url_for("dashboard"))

        return "Invalid email or password!", 401

    return render_template("login.html")


# =========================================================
# ADMIN DASHBOARD
# =========================================================

@app.route("/admin")
def admin_dashboard():

    if not login_required():
        return redirect(url_for("login"))

    if not admin_required():
        return "Access Denied", 403

    student = get_current_student()

    courses = Course.query.order_by(
        Course.course_name
    ).all()

    books = Book.query.all()
    students = Student.query.all()

    announcements = Announcement.query.order_by(
        Announcement.created_at.desc()
    ).all()

    course_data = []

    for course in courses:

        registered_count = Enrollment.query.filter_by(
            course_id=course.course_id
        ).count()

        course_data.append({
            "course": course,
            "registered_count": registered_count,
            "available_seats": max(
                course.capacity - registered_count, 0
            )
        })

    return render_template(
        "admin_dashboard.html",
        student=student,
        courses=courses,
        course_data=course_data,
        books=books,
        students=students,
        announcements=announcements
    )


# =========================================================
# ADMIN: ADD COURSE
# =========================================================

@app.route("/admin/add-course", methods=["GET", "POST"])
def admin_add_course():

    if not login_required():
        return redirect(url_for("login"))

    if not admin_required():
        return "Access Denied", 403

    error = None

    if request.method == "POST":

        course_name = request.form.get(
            "course_name", ""
        ).strip()

        department = request.form.get(
            "department", ""
        ).strip()

        credits_input = request.form.get(
            "credits", ""
        ).strip()

        capacity_input = request.form.get(
            "capacity", ""
        ).strip()

        credits = None
        capacity = None

        if not all([
            course_name,
            department,
            credits_input,
            capacity_input
        ]):
            error = "Please fill in all fields."

        else:
            try:
                credits = int(credits_input)
                capacity = int(capacity_input)

                if credits <= 0 or capacity <= 0:
                    error = (
                        "Credits and capacity must be "
                        "greater than zero."
                    )

            except ValueError:
                error = (
                    "Credits and capacity must be "
                    "valid whole numbers."
                )

        if error is None:

            existing_course = Course.query.filter_by(
                course_name=course_name,
                department=department
            ).first()

            if existing_course:
                error = (
                    "This course already exists "
                    "in this department."
                )

        if error is None:

            course = Course(
                course_name=course_name,
                department=department,
                credits=credits,
                capacity=capacity
            )

            try:
                db.session.add(course)
                db.session.commit()

                return redirect(
                    url_for("admin_dashboard")
                )

            except SQLAlchemyError:
                db.session.rollback()
                app.logger.exception(
                    "Course creation failed."
                )
                error = "Could not save the course."

    return render_template(
        "add_course.html",
        error=error
    )


# =========================================================
# ADMIN: DELETE COURSE
# =========================================================

@app.route(
    "/admin/delete-course/<int:course_id>",
    methods=["POST"]
)
def admin_delete_course(course_id):

    if not login_required():
        return redirect(url_for("login"))

    if not admin_required():
        return "Access Denied", 403

    course = db.session.get(Course, course_id)

    if not course:
        return "Course not found!", 404

    try:
        # Delete related exam records.
        CertificationExam.query.filter_by(
            course_id=course_id
        ).delete(synchronize_session=False)

        # Delete student enrollments.
        Enrollment.query.filter_by(
            course_id=course_id
        ).delete(synchronize_session=False)

        # Delete study-material database records.
        Book.query.filter_by(
            course_id=course_id
        ).delete(synchronize_session=False)

        db.session.delete(course)
        db.session.commit()

    except SQLAlchemyError:
        db.session.rollback()
        app.logger.exception(
            "Course deletion failed."
        )
        return "Could not delete the course.", 500

    return redirect(url_for("admin_dashboard"))


# =========================================================
# ADMIN: UPDATE COURSE CAPACITY
# =========================================================

@app.route(
    "/admin/update-capacity/<int:course_id>",
    methods=["POST"]
)
def admin_update_capacity(course_id):

    if not login_required():
        return redirect(url_for("login"))

    if not admin_required():
        return "Access Denied", 403

    course = db.session.get(Course, course_id)

    if not course:
        return "Course not found!", 404

    try:
        new_capacity = int(
            request.form.get("capacity", "")
        )

        if new_capacity <= 0:
            return (
                "Capacity must be greater than zero.",
                400
            )

    except (ValueError, TypeError):
        return "Enter a valid capacity.", 400

    registered_count = Enrollment.query.filter_by(
        course_id=course_id
    ).count()

    if new_capacity < registered_count:
        return (
            f"Capacity cannot be less than the "
            f"{registered_count} students already registered.",
            400
        )

    try:
        course.capacity = new_capacity
        db.session.commit()

    except SQLAlchemyError:
        db.session.rollback()
        app.logger.exception(
            "Capacity update failed."
        )
        return "Could not update capacity.", 500

    return redirect(url_for("admin_dashboard"))


# =========================================================
# ADMIN: PUBLISH ANNOUNCEMENT
# =========================================================

@app.route(
    "/admin/add-announcement",
    methods=["POST"]
)
def admin_add_announcement():

    if not login_required():
        return redirect(url_for("login"))

    if not admin_required():
        return "Access Denied", 403

    title = request.form.get(
        "title", ""
    ).strip()

    message = request.form.get(
        "message", ""
    ).strip()

    if not title or not message:
        return (
            "Announcement title and message are required.",
            400
        )

    if len(title) > 200:
        return "Title must not exceed 200 characters.", 400

    announcement = Announcement(
        title=title,
        message=message
    )

    try:
        db.session.add(announcement)
        db.session.commit()

    except SQLAlchemyError:
        db.session.rollback()
        app.logger.exception(
            "Announcement creation failed."
        )
        return "Could not publish announcement.", 500

    return redirect(url_for("admin_dashboard"))


# =========================================================
# ADMIN: DELETE ANNOUNCEMENT
# =========================================================

@app.route(
    "/admin/delete-announcement/<int:announcement_id>",
    methods=["POST"]
)
def admin_delete_announcement(announcement_id):

    if not login_required():
        return redirect(url_for("login"))

    if not admin_required():
        return "Access Denied", 403

    announcement = db.session.get(
        Announcement,
        announcement_id
    )

    if not announcement:
        return "Announcement not found!", 404

    try:
        db.session.delete(announcement)
        db.session.commit()

    except SQLAlchemyError:
        db.session.rollback()
        app.logger.exception(
            "Announcement deletion failed."
        )
        return "Could not delete announcement.", 500

    return redirect(url_for("admin_dashboard"))


# =========================================================
# ADMIN: UPLOAD STUDY MATERIAL PDF
# =========================================================

@app.route(
    "/admin/upload-book",
    methods=["GET", "POST"]
)
def admin_upload_book():

    if not login_required():
        return redirect(url_for("login"))

    if not admin_required():
        return "Access Denied", 403

    courses = Course.query.order_by(
        Course.course_name
    ).all()

    if request.method == "POST":

        course_id = request.form.get("course_id")
        book_name = request.form.get(
            "book_name", ""
        ).strip()
        description = request.form.get(
            "description", ""
        ).strip()
        file = request.files.get("file")

        if not course_id or not book_name or not file:
            return (
                "Please complete all required fields.",
                400
            )

        course = db.session.get(Course, course_id)

        if not course:
            return "Course not found.", 404

        if not file.filename:
            return "Please select a PDF file.", 400

        if not allowed_file(file.filename):
            return "Only PDF files are allowed.", 400

        filename = secure_filename(file.filename)

        if not filename:
            return "Invalid filename.", 400

        upload_folder = app.config["UPLOAD_FOLDER"]
        os.makedirs(upload_folder, exist_ok=True)

        # Avoid overwriting a PDF with the same filename.
        original_name, extension = os.path.splitext(filename)
        counter = 1

        while os.path.exists(
            os.path.join(upload_folder, filename)
        ):
            filename = (
                f"{original_name}_{counter}{extension}"
            )
            counter += 1

        file_path = os.path.join(
            upload_folder, filename
        )

        try:
            file.save(file_path)

            book = Book(
                course_id=course.course_id,
                book_name=book_name,
                description=description,
                file_path=f"books/{filename}"
            )

            db.session.add(book)
            db.session.commit()

        except (OSError, SQLAlchemyError):
            db.session.rollback()

            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except OSError:
                    app.logger.exception(
                        "Could not remove uploaded file."
                    )

            app.logger.exception(
                "Study material upload failed."
            )
            return "Could not upload study material.", 500

        return redirect(url_for("admin_dashboard"))

    return render_template(
        "admin_upload_book.html",
        courses=courses
    )


# =========================================================
# STUDENT DASHBOARD
# =========================================================

@app.route("/dashboard")
def dashboard():

    if not login_required():
        return redirect(url_for("login"))

    if session.get("role") == "admin":
        return redirect(url_for("admin_dashboard"))

    announcements = Announcement.query.order_by(
        Announcement.created_at.desc()
    ).all()

    # Preserve the existing dashboard template and styling.
    return render_template(
        "dashboard.html",
        student_name=session.get(
            "student_name", "Student"
        ),
        announcements=announcements
    )


# =========================================================
# AVAILABLE COURSES + SEARCH
# =========================================================

@app.route("/courses")
def courses():

    if not login_required():
        return redirect(url_for("login"))

    search_query = request.args.get(
        "search", ""
    ).strip()

    all_courses = Course.query.order_by(
        Course.course_name
    ).all()

    if search_query:
        search_text = search_query.casefold()

        searchable_fields = (
            "course_name",
            "name",
            "title",
            "topic",
            "category",
            "description",
            "department"
        )

        filtered_courses = []

        for course in all_courses:

            searchable_values = [
                str(getattr(course, field, "") or "")
                for field in searchable_fields
            ]

            if any(
                search_text in value.casefold()
                for value in searchable_values
            ):
                filtered_courses.append(course)

        all_courses = filtered_courses

    course_data = []

    for course in all_courses:

        registered_count = Enrollment.query.filter_by(
            course_id=course.course_id
        ).count()

        available_seats = max(
            course.capacity - registered_count, 0
        )

        course_data.append({
            "course": course,
            "registered_count": registered_count,
            "available_seats": available_seats
        })

    return render_template(
        "courses.html",
        course_data=course_data,
        search_query=search_query
    )


# =========================================================
# REGISTER FOR A COURSE
# =========================================================

@app.route("/register-course/<int:course_id>")
def register_course(course_id):

    if not login_required():
        return redirect(url_for("login"))

    if session.get("role") == "admin":
        return "Admins cannot register as students.", 403

    student_id = session["student_id"]

    course = db.session.get(Course, course_id)

    if not course:
        return "Course not found!", 404

    existing_enrollment = Enrollment.query.filter_by(
        student_id=student_id,
        course_id=course_id
    ).first()

    if existing_enrollment:
        return "You are already registered for this course!"

    registered_count = Enrollment.query.filter_by(
        course_id=course_id
    ).count()

    if registered_count >= course.capacity:
        return "Sorry, this course is full!"

    enrollment = Enrollment(
        student_id=student_id,
        course_id=course_id
    )

    try:
        db.session.add(enrollment)
        db.session.commit()

    except SQLAlchemyError:
        db.session.rollback()
        app.logger.exception(
            "Course registration failed."
        )
        return "Could not register for this course.", 500

    return redirect(url_for("my_courses"))


# =========================================================
# MY COURSES
# =========================================================

@app.route("/my-courses")
def my_courses():

    if not login_required():
        return redirect(url_for("login"))

    student_id = session["student_id"]

    enrollments = Enrollment.query.filter_by(
        student_id=student_id
    ).all()

    paid_exams = CertificationExam.query.filter_by(
        student_id=student_id,
        payment_status="Paid"
    ).all()

    registered_exam_course_ids = {
        exam.course_id for exam in paid_exams
    }

    return render_template(
        "my_courses.html",
        enrollments=enrollments,
        registered_exam_course_ids=(
            registered_exam_course_ids
        )
    )


# =========================================================
# DROP COURSE
# =========================================================

@app.route("/drop-course/<int:course_id>")
def drop_course(course_id):

    if not login_required():
        return redirect(url_for("login"))

    if session.get("role") == "admin":
        return "Admins cannot drop student courses.", 403

    student_id = session["student_id"]

    enrollment = Enrollment.query.filter_by(
        student_id=student_id,
        course_id=course_id
    ).first()

    if not enrollment:
        return "You are not registered for this course!"

    try:
        db.session.delete(enrollment)
        db.session.commit()

    except SQLAlchemyError:
        db.session.rollback()
        app.logger.exception("Course drop failed.")
        return "Could not drop this course.", 500

    return redirect(url_for("my_courses"))


# =========================================================
# EXTERNAL COURSES
# =========================================================

@app.route("/external-courses")
def external_courses():

    if not login_required():
        return redirect(url_for("login"))

    selected_category = request.args.get("category")

    query = ExternalCourse.query.filter_by(
        is_active=True
    )

    if selected_category:
        query = query.filter_by(
            category=selected_category
        )

    external_course_list = query.order_by(
        ExternalCourse.course_name
    ).all()

    categories = [
        "Data Analytics",
        "AI",
        "Engineering",
        "Product Management",
        "Cyber Security",
        "Project Management",
        "Supply Chain & Logistics"
    ]

    return render_template(
        "external_courses.html",
        external_courses=external_course_list,
        categories=categories,
        selected_category=selected_category
    )


# =========================================================
# CERTIFICATION EXAM REGISTRATION
# =========================================================

@app.route("/register-exam/<int:course_id>")
def register_exam(course_id):

    if not login_required():
        return redirect(url_for("login"))

    if session.get("role") == "admin":
        return "Admins cannot register for student exams.", 403

    student_id = session["student_id"]

    course = db.session.get(Course, course_id)

    if not course:
        return "Course not found!", 404

    enrollment = Enrollment.query.filter_by(
        student_id=student_id,
        course_id=course_id
    ).first()

    if not enrollment:
        return (
            "You must register for the course first!"
        )

    existing_exam = CertificationExam.query.filter_by(
        student_id=student_id,
        course_id=course_id
    ).first()

    exam_fee = 100

    if existing_exam:
        return render_template(
            "exam_payment.html",
            course=course,
            exam=existing_exam,
            exam_fee=existing_exam.exam_fee
        )

    return render_template(
        "exam_payment.html",
        course=course,
        exam=None,
        exam_fee=exam_fee
    )


# =========================================================
# CONFIRM EXAM PAYMENT
# =========================================================

@app.route(
    "/confirm-exam-payment/<int:course_id>",
    methods=["POST"]
)
def confirm_exam_payment(course_id):

    if not login_required():
        return redirect(url_for("login"))

    if session.get("role") == "admin":
        return "Admins cannot register for student exams.", 403

    student_id = session["student_id"]

    course = db.session.get(Course, course_id)

    if not course:
        return "Course not found!", 404

    enrollment = Enrollment.query.filter_by(
        student_id=student_id,
        course_id=course_id
    ).first()

    if not enrollment:
        return (
            "You must register for the course first!"
        )

    existing_exam = CertificationExam.query.filter_by(
        student_id=student_id,
        course_id=course_id
    ).first()

    try:
        if existing_exam:

            if existing_exam.payment_status == "Paid":
                return redirect(
                    url_for(
                        "exam_success",
                        exam_id=existing_exam.exam_id
                    )
                )

            existing_exam.payment_status = "Paid"
            existing_exam.registration_status = "Registered"

            db.session.commit()

            return redirect(
                url_for(
                    "exam_success",
                    exam_id=existing_exam.exam_id
                )
            )

        exam = CertificationExam(
            student_id=student_id,
            course_id=course_id,
            exam_fee=100,
            payment_status="Paid",
            registration_status="Registered"
        )

        db.session.add(exam)
        db.session.commit()

    except SQLAlchemyError:
        db.session.rollback()
        app.logger.exception(
            "Exam registration failed."
        )
        return "Could not register for the exam.", 500

    return redirect(
        url_for(
            "exam_success",
            exam_id=exam.exam_id
        )
    )


# =========================================================
# EXAM SUCCESS
# =========================================================

@app.route("/exam-success/<int:exam_id>")
def exam_success(exam_id):

    if not login_required():
        return redirect(url_for("login"))

    exam = db.session.get(
        CertificationExam, exam_id
    )

    if not exam:
        return "Exam registration not found!", 404

    # Students may only view their own exam registration.
    if (
        session.get("role") != "admin"
        and exam.student_id != session["student_id"]
    ):
        return "Access Denied", 403

    return render_template(
        "exam_success.html",
        exam=exam
    )


# =========================================================
# MY PROFILE
# =========================================================

@app.route("/profile")
def profile():

    if not login_required():
        return redirect(url_for("login"))

    student_id = session["student_id"]

    student = db.session.get(Student, student_id)

    if not student:
        return "Student not found!", 404

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

    if not login_required():
        return redirect(url_for("login"))

    student_id = session["student_id"]

    student = db.session.get(Student, student_id)

    if not student:
        return "Student not found!", 404

    if request.method == "POST":

        name = request.form.get("name", "").strip()
        department = request.form.get(
            "department", ""
        ).strip()
        year = request.form.get("year", "").strip()

        if not all([name, department, year]):
            return "Please fill in all fields.", 400

        student.name = name
        student.department = department
        student.year = year

        try:
            db.session.commit()

        except SQLAlchemyError:
            db.session.rollback()
            app.logger.exception(
                "Profile update failed."
            )
            return "Could not update profile.", 500

        session["student_name"] = name

        return redirect(url_for("profile"))

    return render_template(
        "edit_profile.html",
        student=student
    )


# =========================================================
# LOGOUT
# =========================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("login"))


# =========================================================
# RUN APPLICATION
# =========================================================

if __name__ == "__main__":
    app.run(debug=True)