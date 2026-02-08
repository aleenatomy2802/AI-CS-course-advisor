"""
Course Importer - Web scraping script for Texas State CS catalog
"""

import requests
from bs4 import BeautifulSoup
import re
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('course_importer')

def extract_prerequisites(html_description):
    """Extract prerequisite course codes from HTML"""
    if not html_description:
        return []
    
    prerequisites = []
    soup = BeautifulSoup(html_description, "html.parser")
    
    if "prerequisite:" in soup.get_text().lower():
        anchors = soup.find_all("a", class_="bubblelink code")
        for a in anchors:
            course_code = a.get_text(strip=True).replace("\xa0", " ")
            prerequisites.append(course_code)
    
    if not prerequisites:
        backup_pattern = r'[Pp]rerequisites?:\s*([A-Z]{2,4}\s+\d{3}[A-Z]?)'
        backup_matches = re.findall(backup_pattern, html_description)
        prerequisites.extend(backup_matches)
    
    return prerequisites

def import_courses_from_website(url="https://mycatalog.txstate.edu/courses/cs/"):
    """Import courses from catalog website"""
    from app import app, db
    from models import Course, CoursePrerequisite
    
    try:
        with app.app_context():
            logger.info(f"Fetching courses from {url}")
            response = requests.get(url)
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
                    match = re.match(r'([A-Za-z]+)\s+(\d+[A-Za-z]?)\.?\s+(.*)', course_title)
                    if not match:
                        continue
                    
                    dept_code = match.group(1)
                    course_number = match.group(2)
                    course_name = match.group(3)
                    
                    desc_elem = block.find('p', class_='courseblockdesc')
                    description = str(desc_elem) if desc_elem else ""
                    
                    course_level = 1
                    try:
                        num = int(course_number[:3])
                        if num < 200:
                            course_level = 1
                        elif num < 300:
                            course_level = 2
                        elif num < 400:
                            course_level = 3
                        else:
                            course_level = 4
                    except:
                        pass

                    full_name = f"{dept_code} {course_number}: {course_name}"
                    course_code = f"{dept_code} {course_number}"
                    prereqs = extract_prerequisites(description)
                    
                    courses_data.append({
                        'code': course_code,
                        'name': full_name,
                        'description': description,
                        'department': dept_code,
                        'level': course_level,
                        'prerequisites': prereqs
                    })
                    
                    logger.info(f"Processed: {course_code}")
                
                except Exception as e:
                    logger.error(f"Error processing course: {e}")
            
            # Clear existing data
            db.session.query(CoursePrerequisite).delete()
            db.session.query(Course).delete()
            db.session.commit()
            
            # Insert courses
            course_ids = {}
            for course_data in courses_data:
                course = Course(
                    name=course_data['name'],
                    description=course_data['description'],
                    department=course_data['department'],
                    level=course_data['level']
                )
                db.session.add(course)
                db.session.flush()
                course_ids[course_data['code']] = course.id
            
            db.session.commit()
            
            # Create prerequisite relationships (avoid duplicates)
            prereq_pairs = set()  # Track (course_id, prerequisite_id) pairs
            for course_data in courses_data:
                course_id = course_ids[course_data['code']]
                for prereq_code in course_data['prerequisites']:
                    if prereq_code in course_ids:
                        prereq_id = course_ids[prereq_code]
                        pair = (course_id, prereq_id)
                        
                        # Only add if not already added
                        if pair not in prereq_pairs:
                            prereq_relation = CoursePrerequisite(
                                course_id=course_id,
                                prerequisite_id=prereq_id
                            )
                            db.session.add(prereq_relation)
                            prereq_pairs.add(pair)
            
            db.session.commit()
            
            course_count = db.session.query(Course).count()
            prereq_count = db.session.query(CoursePrerequisite).count()
            
            logger.info(f"✅ Imported {course_count} courses, {prereq_count} prerequisites")
            
            return {
                "success": True,
                "course_count": course_count,
                "prerequisite_count": prereq_count
            }
    
    except Exception as e:
        logger.error(f"Error importing courses: {e}")
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    result = import_courses_from_website()
    if result["success"]:
        print(f"✅ Successfully imported {result['course_count']} courses")
    else:
        print(f"❌ Error: {result['error']}")