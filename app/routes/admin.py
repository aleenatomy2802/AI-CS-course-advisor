"""
Admin routes — private analytics dashboard.
Protected by ADMIN_SECRET env variable.
Access: /admin/logs?secret=YOUR_SECRET
"""

import os
import logging
from flask import Blueprint, request, jsonify, render_template_string
from app.models.chat_log import ChatLog

logger = logging.getLogger('routes.admin')
bp = Blueprint('admin', __name__)

ADMIN_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Chat Logs — Admin</title>
    <style>
        body { font-family: sans-serif; max-width: 1000px; margin: 2rem auto; padding: 0 1rem; }
        h1 { color: #501214; }
        .stats { display: flex; gap: 2rem; margin: 1rem 0 2rem; }
        .stat { background: #f5f1ee; padding: 1rem 1.5rem; border-radius: 8px; }
        .stat strong { display: block; font-size: 2rem; color: #501214; }
        table { width: 100%; border-collapse: collapse; font-size: 0.9rem; }
        th { background: #501214; color: white; padding: 10px 12px; text-align: left; }
        td { padding: 10px 12px; border-bottom: 1px solid #eee; vertical-align: top; }
        tr:hover td { background: #fafafa; }
        .ok { color: green; }
        .fail { color: red; }
        .q { font-weight: 600; }
        .a { color: #666; font-size: 0.82rem; margin-top: 4px; }
    </style>
</head>
<body>
    <h1>Chat Logs</h1>
    <div class="stats">
        <div class="stat"><strong>{{ total }}</strong>Total questions</div>
        <div class="stat"><strong>{{ success_rate }}%</strong>Gemini success rate</div>
        <div class="stat"><strong>{{ today }}</strong>Today</div>
    </div>
    <table>
        <tr>
            <th>#</th><th>Time</th><th>Question / Answer preview</th><th>Status</th>
        </tr>
        {% for log in logs %}
        <tr>
            <td>{{ log.id }}</td>
            <td style="white-space:nowrap; color:#888;">{{ log.created_at.strftime('%m/%d %H:%M') }}</td>
            <td>
                <div class="q">{{ log.question }}</div>
                <div class="a">{{ log.answer[:120] }}{% if log.answer|length > 120 %}…{% endif %}</div>
            </td>
            <td class="{{ 'ok' if log.success else 'fail' }}">
                {{ '✓ AI' if log.success else '✗ basic' }}
            </td>
        </tr>
        {% endfor %}
    </table>
    {% if not logs %}<p style="color:#888; margin-top:2rem;">No chat logs yet.</p>{% endif %}
</body>
</html>
"""


@bp.route('/admin/logs')
def admin_logs():
    """View all chat logs. Protected by ?secret= query param."""
    secret = os.environ.get('ADMIN_SECRET', '')
    if not secret or request.args.get('secret') != secret:
        return jsonify({"error": "Unauthorized"}), 401

    from datetime import datetime, timezone, timedelta
    logs  = ChatLog.query.order_by(ChatLog.created_at.desc()).limit(200).all()
    total = ChatLog.query.count()
    success_count = ChatLog.query.filter_by(success=True).count()
    success_rate  = round(success_count / total * 100) if total else 0

    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0)
    today_count = ChatLog.query.filter(ChatLog.created_at >= today_start).count()

    return render_template_string(
        ADMIN_HTML,
        logs=logs,
        total=total,
        success_rate=success_rate,
        today=today_count,
    )


@bp.route('/admin/patch-prereqs')
def patch_prereqs():
    """Manually patch known prerequisites in the database. Run once after deploy."""
    secret = os.environ.get('ADMIN_SECRET', '')
    if not secret or request.args.get('secret') != secret:
        return jsonify({"error": "Unauthorized"}), 401

    from app.extensions import db
    from app.models import Course, CoursePrerequisite

    PREREQ_MAP = {
        "CS 2308": ["CS 1428"],
        "CS 2315": ["CS 1428"],
        "CS 2318": ["CS 2308"],
        "CS 3339": ["CS 2308", "CS 2318"],
        "CS 3354": ["CS 3358"],
        "CS 3358": ["CS 2308"],
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
        "CS 4347": ["CS 3358"],
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

    added, skipped, not_found = 0, 0, []

    for course_code, prereq_codes in PREREQ_MAP.items():
        course = Course.query.filter(Course.name.ilike(f"{course_code}%")).first()
        if not course:
            not_found.append(course_code)
            continue
        for prereq_code in prereq_codes:
            prereq = Course.query.filter(Course.name.ilike(f"{prereq_code}%")).first()
            if not prereq:
                not_found.append(f"{prereq_code} (prereq of {course_code})")
                continue
            existing = CoursePrerequisite.query.filter_by(
                course_id=course.id, prerequisite_id=prereq.id
            ).first()
            if existing:
                skipped += 1
            else:
                db.session.add(CoursePrerequisite(
                    course_id=course.id, prerequisite_id=prereq.id
                ))
                added += 1

    db.session.commit()
    return jsonify({
        "status": "done",
        "added": added,
        "skipped": skipped,
        "not_found": not_found,
    })
