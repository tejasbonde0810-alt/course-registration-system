from extensions import db


class Book(db.Model):
    __tablename__ = "books"

    book_id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True
    )

    course_id = db.Column(
        db.Integer,
        db.ForeignKey("courses.course_id"),
        nullable=False
    )

    book_name = db.Column(
        db.String(200),
        nullable=False
    )

    description = db.Column(
        db.Text,
        nullable=True
    )

    file_path = db.Column(
        db.String(500),
        nullable=False
    )

    course = db.relationship(
        "Course",
        backref=db.backref(
            "books",
            lazy=True
        )
    )