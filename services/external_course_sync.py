from datetime import datetime

from extensions import db
from models.external_course import ExternalCourse


# =========================================================
# ALLOWED COURSE CATEGORIES
# =========================================================

ALLOWED_CATEGORIES = {
    "Data Analytics",
    "AI",
    "Engineering",
    "Product Management",
    "Cyber Security",
    "Project Management",
    "Supply Chain & Logistics"
}


# =========================================================
# NORMALIZE CATEGORY
# =========================================================

def normalize_category(category):

    if not category:
        return None

    category = category.strip().lower()

    category_map = {

        "data analytics": "Data Analytics",
        "data & analytics": "Data Analytics",
        "data": "Data Analytics",

        "ai": "AI",
        "artificial intelligence": "AI",
        "machine learning": "AI",

        "engineering": "Engineering",

        "product management": "Product Management",

        "cyber security": "Cyber Security",
        "cybersecurity": "Cyber Security",
        "security": "Cyber Security",

        "project management": "Project Management",

        "supply chain": "Supply Chain & Logistics",
        "supply chain & logistics": "Supply Chain & Logistics",
        "logistics": "Supply Chain & Logistics"
    }

    return category_map.get(category)


# =========================================================
# ADD OR UPDATE ONE EXTERNAL COURSE
# =========================================================

def upsert_external_course(course_data):

    course_name = course_data.get("course_name")
    provider = course_data.get("provider")
    course_url = course_data.get("course_url")

    # -----------------------------------------------------
    # Required fields
    # -----------------------------------------------------

    if not course_name:
        return False

    if not provider:
        return False

    if not course_url:
        return False

    # -----------------------------------------------------
    # Normalize category
    # -----------------------------------------------------

    category = normalize_category(
        course_data.get("category")
    )

    # -----------------------------------------------------
    # Reject unsupported categories
    # -----------------------------------------------------

    if category not in ALLOWED_CATEGORIES:
        return False

    # -----------------------------------------------------
    # Check whether course already exists
    # -----------------------------------------------------

    existing_course = ExternalCourse.query.filter_by(
        course_url=course_url
    ).first()

    # =====================================================
    # UPDATE EXISTING COURSE
    # =====================================================

    if existing_course:

        existing_course.course_name = course_name

        existing_course.category = category

        existing_course.provider = provider

        existing_course.description = course_data.get(
            "description"
        )

        existing_course.duration = course_data.get(
            "duration"
        )

        existing_course.expires_at = course_data.get(
            "expires_at"
        )

        existing_course.is_active = True

        existing_course.updated_at = datetime.utcnow()

    # =====================================================
    # ADD NEW COURSE
    # =====================================================

    else:

        new_course = ExternalCourse(

            category=category,

            course_name=course_name,

            provider=provider,

            description=course_data.get(
                "description"
            ),

            course_url=course_url,

            duration=course_data.get(
                "duration"
            ),

            expires_at=course_data.get(
                "expires_at"
            ),

            is_active=True

        )

        db.session.add(new_course)

    return True


# =========================================================
# SYNCHRONIZE EXTERNAL COURSES
# =========================================================

def synchronize_external_courses(course_list):

    added_or_updated = 0

    for course_data in course_list:

        success = upsert_external_course(
            course_data
        )

        if success:

            added_or_updated += 1

    # -----------------------------------------------------
    # Save changes to database
    # -----------------------------------------------------

    db.session.commit()

    return added_or_updated