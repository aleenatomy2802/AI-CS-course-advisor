"""
One-time script to manually patch missing prerequisites in the local database.
Run once: python patch_prerequisites.py
Safe to run multiple times (uses get_or_create logic).
"""

from wsgi import app
from app.extensions import db
from app.models import Course, CoursePrerequisite

# Known correct prerequisites based on TXST catalog
# Only CS courses listed — MATH/COMM/ENG/PHIL courses are not in the CS-only database
# Format: "COURSE_CODE_PREFIX": ["PREREQ_CODE_PREFIX_1", ...]
PREREQ_MAP = {
    "CS 2308": ["CS 1428"],
    "CS 2315": ["CS 1428"],                        # COMM/ENG/PHIL prereqs not in CS DB
    "CS 2318": ["CS 2308"],                        # MATH 2358 not in CS DB
    "CS 3339": ["CS 2308", "CS 2318"],
    "CS 3354": ["CS 3358"],
    "CS 3358": ["CS 2308"],                        # MATH 2358 not in CS DB
    "CS 3360": ["CS 2318", "CS 3358"],
    "CS 3398": ["CS 3354", "CS 3358", "CS 2315"],
    "CS 4310": ["CS 3360"],
    "CS 4315": ["CS 3358"],
    "CS 4318": ["CS 3358"],
    "CS 4326": ["CS 3358"],
    "CS 4328": ["CS 3339", "CS 3360"],
    "CS 4332": ["CS 3358"],
    "CS 4337": ["CS 3358"],
    "CS 4346": ["CS 3358"],
    "CS 4347": ["CS 3358"],                        # MATH 3305 not in CS DB
    "CS 4350": ["CS 3358"],
    "CS 4353": ["CS 3358"],
    "CS 4355": ["CS 3358"],
    "CS 4371": ["CS 3358"],
    "CS 4372": ["CS 3358"],
    "CS 4379D": ["CS 3358"],
    "CS 4379E": ["CS 3358"],
    "CS 4379F": ["CS 3354", "CS 3358"],
    "CS 4379G": ["CS 2308"],
    "CS 4379H": ["CS 3358"],
    "CS 4379K": ["CS 3358"],
    "CS 4379Q": ["CS 3358"],
    "CS 4380": ["CS 3339", "CS 3360"],
    "CS 4381": ["CS 3398"],
    "CS 4388": ["CS 3358"],
    "CS 4398": ["CS 3398"],
}


def patch():
    with app.app_context():
        added = 0
        skipped = 0
        not_found = []

        for course_prefix, prereq_prefixes in PREREQ_MAP.items():
            # Find the course (match by name starting with the code)
            course = Course.query.filter(Course.name.ilike(f"{course_prefix}%")).first()
            if not course:
                not_found.append(course_prefix)
                continue

            for prereq_prefix in prereq_prefixes:
                prereq = Course.query.filter(Course.name.ilike(f"{prereq_prefix}%")).first()
                if not prereq:
                    not_found.append(f"{prereq_prefix} (prereq of {course_prefix})")
                    continue

                # Check if already exists
                existing = CoursePrerequisite.query.filter_by(
                    course_id=course.id,
                    prerequisite_id=prereq.id
                ).first()

                if existing:
                    skipped += 1
                else:
                    db.session.add(CoursePrerequisite(
                        course_id=course.id,
                        prerequisite_id=prereq.id
                    ))
                    added += 1
                    print(f"  + {course.name}  ←requires—  {prereq.name}")

        db.session.commit()
        print(f"\nDone: {added} added, {skipped} already existed")
        if not_found:
            print(f"Not found in DB: {not_found}")


if __name__ == "__main__":
    patch()
