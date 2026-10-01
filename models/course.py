from extensions import db


class Course(db.Model):
    __tablename__ = "courses"

    course_id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True
    )

    course_name = db.Column(
        db.String(100),
        nullable=False
    )

    department = db.Column(
        db.String(50)
    )

    credits = db.Column(
        db.Integer,
        nullable=False
    )

    capacity = db.Column(
        db.Integer,
        nullable=False
    )