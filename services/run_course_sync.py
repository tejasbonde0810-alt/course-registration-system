import sys
import os

# Add project root to Python path
sys.path.insert(
    0,
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )
)

from app import app

from services.course_data_source import (
    get_external_courses
)

from services.external_course_sync import (
    synchronize_external_courses
)


# =========================================================
# RUN EXTERNAL COURSE SYNCHRONIZATION
# =========================================================

def run_sync():

    print(
        "Starting external course synchronization..."
    )

    courses = get_external_courses()

    print(
        f"Courses received from source: {len(courses)}"
    )

    with app.app_context():

        count = synchronize_external_courses(
            courses
        )

    print(
        f"Courses added/updated: {count}"
    )

    print(
        "Synchronization completed."
    )


# =========================================================
# RUN APPLICATION
# =========================================================

if __name__ == "__main__":

    run_sync()