from extensions import db
from datetime import date


class Enrollment(db.Model):

    __tablename__ = "enrollments"

    enrollment_id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True
    )

    student_id = db.Column(
        db.Integer,
        db.ForeignKey("students.student_id"),
        nullable=False
    )

    course_id = db.Column(
        db.Integer,
        db.ForeignKey("courses.course_id"),
        nullable=False
    )

    enrollment_date = db.Column(
        db.Date,
        nullable=False,
        default=date.today
    )

    status = db.Column(
        db.String(20),
        default="Registered"
    )

    # Relationship with Course
    course = db.relationship(
        "Course",
        backref="enrollments"
    )