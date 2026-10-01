from extensions import db


class Student(db.Model):
    __tablename__ = "students"

    student_id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True
    )

    name = db.Column(
        db.String(100),
        nullable=False
    )

    email = db.Column(
        db.String(100),
        unique=True,
        nullable=False
    )

    password = db.Column(
        db.String(255),
        nullable=False
    )

    department = db.Column(
        db.String(50)
    )

    year = db.Column(
        db.Integer
    )