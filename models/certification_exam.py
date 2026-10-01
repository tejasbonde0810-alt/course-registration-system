from extensions import db
from datetime import date


class CertificationExam(db.Model):

    __tablename__ = "certification_exams"

    exam_id = db.Column(
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

    exam_fee = db.Column(
        db.Numeric(10, 2),
        nullable=False
    )

    payment_status = db.Column(
        db.String(20),
        default="Pending"
    )

    registration_status = db.Column(
        db.String(20),
        default="Pending"
    )

    registration_date = db.Column(
        db.Date,
        nullable=False,
        default=date.today
    )

    course = db.relationship(
        "Course",
        backref="certification_exams"
    )