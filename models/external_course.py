from extensions import db


class ExternalCourse(db.Model):
    __tablename__ = "external_courses"

    external_course_id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True
    )

    category = db.Column(
        db.String(100),
        nullable=False
    )

    course_name = db.Column(
        db.String(200),
        nullable=False
    )

    provider = db.Column(
        db.String(100),
        nullable=False
    )

    description = db.Column(
        db.Text,
        nullable=True
    )

    course_url = db.Column(
        db.String(500),
        nullable=False
    )

    duration = db.Column(
        db.String(100),
        nullable=True
    )

    expires_at = db.Column(
        db.DateTime,
        nullable=True
    )

    is_active = db.Column(
        db.Boolean,
        default=True,
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        server_default=db.func.now()
    )

    updated_at = db.Column(
        db.DateTime,
        server_default=db.func.now(),
        onupdate=db.func.now()
    )