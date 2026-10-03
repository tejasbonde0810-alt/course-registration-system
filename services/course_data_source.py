import os
import requests


# =========================================================
# GET EXTERNAL COURSE API URL
# =========================================================

API_URL = os.environ.get(
    "EXTERNAL_COURSE_API_URL"
)


# =========================================================
# GET COURSES FROM EXTERNAL API
# =========================================================

def get_external_courses():

    # -----------------------------------------------------
    # Check whether API URL is configured
    # -----------------------------------------------------

    if not API_URL:

        print(
            "EXTERNAL_COURSE_API_URL is not configured."
        )

        return []

    try:

        # -------------------------------------------------
        # Send request to external API
        # -------------------------------------------------

        response = requests.get(
            API_URL,
            timeout=20
        )

        # -------------------------------------------------
        # Stop if API returns an error
        # -------------------------------------------------

        response.raise_for_status()

        # -------------------------------------------------
        # Convert JSON response
        # -------------------------------------------------

        data = response.json()

        # -------------------------------------------------
        # Handle APIs that return a list directly
        # -------------------------------------------------

        if isinstance(data, list):

            return data

        # -------------------------------------------------
        # Handle APIs that return:
        #
        # {
        #     "courses": [...]
        # }
        # -------------------------------------------------

        if isinstance(data, dict):

            courses = data.get(
                "courses",
                []
            )

            if isinstance(courses, list):

                return courses

        print(
            "Unexpected API response format."
        )

        return []

    # -----------------------------------------------------
    # Connection / request error
    # -----------------------------------------------------

    except requests.exceptions.RequestException as error:

        print(
            "External course API request failed:"
        )

        print(error)

        return []

    # -----------------------------------------------------
    # Invalid JSON
    # -----------------------------------------------------

    except ValueError as error:

        print(
            "API returned invalid JSON:"
        )

        print(error)

        return []