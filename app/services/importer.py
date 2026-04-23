"""
Course importer service — scrapes the TXST CS catalog and populates the DB.
Single Responsibility: data ingestion only.
"""

import re
import logging

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger('course_importer')


def extract_prerequisites(html_description: str) -> list:
    """Extract prerequisite course codes from a course's HTML description."""
    if not html_description:
        return []

    prerequisites = []
    soup = BeautifulSoup(html_description, "html.parser")

    # Primary: catalog links have class="bubblelink code"
    if "prerequisite:" in soup.get_text().lower():
        anchors = soup.find_all("a", class_="bubblelink code")
        for a in anchors:
            code = a.get_text(strip=True).replace("\xa0", " ")
            prerequisites.append(code)

    # Backup: plain-text extraction when anchor tags are absent
    if not prerequisites:
        text = soup.get_text()
        match = re.search(r'[Pp]rerequisites?:(.+?)(?:\.|$)', text)
        if match:
            prereq_text = match.group(1)
            # TXST uses 4-digit course numbers (e.g. CS 2308, MATH 2358)
            found = re.findall(r'([A-Z]{2,4}\s+\d{4}[A-Z]?)', prereq_text)
            prerequisites.extend(found)

    return prerequisites


def import_courses_from_website(
    url: str = "https://mycatalog.txstate.edu/courses/cs/"
) -> dict:
    """
    Scrape courses from the TXST catalog and (re)populate the database.
    Requires an active Flask application context.
    """
    from app.extensions import db
    from app.models import Course, CoursePrerequisite

    try:
        logger.info(f"Fetching courses from {url}")
        response = requests.get(url, timeout=30)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')
        course_blocks = soup.find_all('div', class_='courseblock')
        logger.info(f"Found {len(course_blocks)} course blocks")

        courses_data = []

        for block in course_blocks:
            try:
                title_elem = block.find('p', class_='courseblocktitle')
                if not title_elem:
                    continue

                course_title = title_elem.get_text(strip=True)
                m = re.match(r'([A-Za-z]+)\s+(\d+[A-Za-z]?)\.?\s+(.*)', course_title)
                if not m:
                    continue

                dept_code     = m.group(1)
                course_number = m.group(2)
                course_name   = m.group(3)

                desc_elem   = block.find('p', class_='courseblockdesc')
                description = str(desc_elem) if desc_elem else ""

                try:
                    num = int(course_number[:3])
                    level = 1 if num < 200 else 2 if num < 300 else 3 if num < 400 else 4
                except ValueError:
                    level = 1

                full_name   = f"{dept_code} {course_number}: {course_name}"
                course_code = f"{dept_code} {course_number}"
                prereqs     = extract_prerequisites(description)

                courses_data.append({
                    'code':          course_code,
                    'name':          full_name,
                    'description':   description,
                    'department':    dept_code,
                    'level':         level,
                    'prerequisites': prereqs,
                })
                logger.info(f"Processed: {course_code}")

            except Exception as e:
                logger.error(f"Error processing course block: {e}")

        # ── Write to database ──────────────────────────────────
        db.session.query(CoursePrerequisite).delete()
        db.session.query(Course).delete()
        db.session.commit()

        course_ids = {}
        for cd in courses_data:
            course = Course(
                name=cd['name'],
                description=cd['description'],
                department=cd['department'],
                level=cd['level'],
            )
            db.session.add(course)
            db.session.flush()
            course_ids[cd['code']] = course.id

        db.session.commit()

        # Prerequisite relationships (deduplicated)
        seen = set()
        for cd in courses_data:
            cid = course_ids[cd['code']]
            for prereq_code in cd['prerequisites']:
                if prereq_code in course_ids:
                    pid  = course_ids[prereq_code]
                    pair = (cid, pid)
                    if pair not in seen:
                        db.session.add(CoursePrerequisite(
                            course_id=cid, prerequisite_id=pid
                        ))
                        seen.add(pair)

        db.session.commit()

        course_count = db.session.query(Course).count()
        prereq_count = db.session.query(CoursePrerequisite).count()
        logger.info(f"Imported {course_count} courses, {prereq_count} prerequisites")

        return {"success": True, "course_count": course_count, "prerequisite_count": prereq_count}

    except Exception as e:
        logger.error(f"Import failed: {e}")
        return {"success": False, "error": str(e)}
