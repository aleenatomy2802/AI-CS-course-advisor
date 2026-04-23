"""
Database models — Course and its prerequisite relationships.
Single Responsibility: data shape only, no business logic.
"""

from app.extensions import db


class Course(db.Model):
    __tablename__ = 'courses'

    id          = db.Column(db.Integer, primary_key=True)
    name        = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    department  = db.Column(db.String(50))
    level       = db.Column(db.Integer)  # 1=Freshman … 4=Senior/Grad

    prerequisites = db.relationship(
        'Course',
        secondary='course_prerequisites',
        primaryjoin='Course.id==CoursePrerequisite.course_id',
        secondaryjoin='Course.id==CoursePrerequisite.prerequisite_id',
        backref='required_for',
    )

    def __repr__(self):
        return f'<Course {self.name}>'

    def to_dict(self):
        return {
            'id':          self.id,
            'name':        self.name,
            'description': self.description,
            'department':  self.department,
            'level':       self.level,
        }


class CoursePrerequisite(db.Model):
    __tablename__ = 'course_prerequisites'

    id              = db.Column(db.Integer, primary_key=True)
    course_id       = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    prerequisite_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)

    __table_args__ = (
        db.UniqueConstraint('course_id', 'prerequisite_id', name='unique_prerequisite'),
    )

    def __repr__(self):
        return f'<CoursePrerequisite {self.course_id} → {self.prerequisite_id}>'
