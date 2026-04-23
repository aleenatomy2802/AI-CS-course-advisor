"""
ChatLog model — stores every question asked through the advisor chat.
Used for analytics: see what students are actually asking.
"""

from datetime import datetime, timezone
from app.extensions import db


class ChatLog(db.Model):
    __tablename__ = 'chat_logs'

    id         = db.Column(db.Integer, primary_key=True)
    question   = db.Column(db.Text, nullable=False)
    answer     = db.Column(db.Text)                    # first 500 chars of response
    success    = db.Column(db.Boolean, default=True)   # False = Gemini fell back to basic mode
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f'<ChatLog {self.id}: {self.question[:40]}>'
