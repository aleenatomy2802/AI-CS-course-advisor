"""
Database models for AI Course Advisor
"""

from extensions import db


class Course(db.Model):
    """Course model representing a CS course"""
    __tablename__ = 'courses'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    department = db.Column(db.String(50))
    level = db.Column(db.Integer)  # 1=Freshman, 2=Sophomore, 3=Junior, 4=Senior/Grad
    
    # Relationships
    prerequisites = db.relationship(
        'Course',
        secondary='course_prerequisites',
        primaryjoin='Course.id==CoursePrerequisite.course_id',
        secondaryjoin='Course.id==CoursePrerequisite.prerequisite_id',
        backref='required_for'
    )

    def __repr__(self):
        return f'<Course {self.name}>'
    
    def to_dict(self):
        """Convert course to dictionary for JSON responses"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'department': self.department,
            'level': self.level
        }


class CoursePrerequisite(db.Model):
    """Many-to-many relationship table for course prerequisites"""
    __tablename__ = 'course_prerequisites'
    
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    prerequisite_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    
    # Unique constraint to prevent duplicate prerequisite relationships
    __table_args__ = (
        db.UniqueConstraint('course_id', 'prerequisite_id', name='unique_prerequisite'),
    )
    
    def __repr__(self):
        return f'<CoursePrerequisite course_id={self.course_id} prereq_id={self.prerequisite_id}>'
