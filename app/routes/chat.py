import logging
from flask import Blueprint, request, jsonify, current_app
from app.extensions import limiter, db
from app.models.chat_log import ChatLog

logger = logging.getLogger('routes.chat')
bp = Blueprint('chat', __name__)


@bp.route('/api/chat', methods=['POST'])
@limiter.limit("20 per minute;100 per hour")
def chat():
    """RAG-powered advisor chat."""
    try:
        data    = request.get_json()
        message = (data or {}).get('message', '').strip()
        user_id = (data or {}).get('user_id', 'anonymous')

        if not message:
            return jsonify({"error": "Message is required"}), 400

        response = current_app.advisor.get_response(user_id, message)

        # ── Log the question + answer snippet ────────────────────────────────
        answer_text = response.get('message', '')
        is_basic    = 'basic mode' in answer_text.lower()
        try:
            log = ChatLog(
                question=message[:1000],          # cap at 1000 chars
                answer=answer_text[:500],          # first 500 chars of reply
                success=not is_basic,
            )
            db.session.add(log)
            db.session.commit()
        except Exception as log_err:
            logger.warning(f"Could not save chat log: {log_err}")
            db.session.rollback()
        # ─────────────────────────────────────────────────────────────────────

        return jsonify(response)

    except Exception as e:
        logger.error(f"Chat error: {e}")
        return jsonify({"error": "I'm having trouble connecting to the advisor."}), 500
