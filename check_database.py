"""
Quick Database Checker - See what's in your database
"""

from app import app, db
from models import Course, CoursePrerequisite

def check_database():
    """Check what's in the database"""
    with app.app_context():
        # Count courses
        course_count = Course.query.count()
        print(f"\n{'='*60}")
        print(f"📚 Total Courses: {course_count}")
        print(f"{'='*60}")
        
        # Count prerequisites
        prereq_count = CoursePrerequisite.query.count()
        print(f"🔗 Total Prerequisite Relationships: {prereq_count}")
        print(f"{'='*60}")
        
        if prereq_count == 0:
            print("\n⚠️  WARNING: No prerequisites found!")
            print("This means the prerequisite relationships weren't imported.")
            print("\nTo fix this, run:")
            print("  python course_importer.py")
            print()
        else:
            print(f"\n✅ Prerequisites imported successfully!")
            print(f"\nShowing 5 example prerequisite relationships:")
            print(f"{'='*60}")
            
            # Show some examples
            prereqs = CoursePrerequisite.query.limit(5).all()
            for p in prereqs:
                course = Course.query.get(p.course_id)
                prereq_course = Course.query.get(p.prerequisite_id)
                print(f"• {course.name}")
                print(f"  └─ Requires: {prereq_course.name}")
                print()
        
        # Check a specific course
        print(f"\n{'='*60}")
        print("Testing CS 4380 (the one you searched):")
        print(f"{'='*60}")
        
        cs4380 = Course.query.filter(Course.name.like('%4380%')).first()
        if cs4380:
            print(f"✅ Found: {cs4380.name}")
            print(f"   Course ID: {cs4380.id}")
            
            # Check its prerequisites
            prereqs = CoursePrerequisite.query.filter_by(course_id=cs4380.id).all()
            print(f"   Prerequisites: {len(prereqs)}")
            
            if len(prereqs) == 0:
                print("   ⚠️  No prerequisites found in database")
            else:
                for p in prereqs:
                    prereq_course = Course.query.get(p.prerequisite_id)
                    print(f"   • {prereq_course.name}")
        else:
            print("❌ CS 4380 not found in database")
        
        print(f"\n{'='*60}\n")

if __name__ == "__main__":
    check_database()
