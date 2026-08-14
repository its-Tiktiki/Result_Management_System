from flask import Blueprint,session
from app.models.teacher import MarksTopic
from flask import jsonify

get_marks_topic_bp = Blueprint(
    "get_marks_topic",
    __name__,
    url_prefix="/get_marks_topic"
)
@get_marks_topic_bp.route("/api/marks-topic/<int:subject_id>")
def api_marks_topic(subject_id):
    if not session.get("teacher"):
        return jsonify([])
    teacher_id = session.get("teacher_id")
    topics = MarksTopic.query.filter_by(
        teacher_id=teacher_id,
        subject_id=subject_id
    ).all()
    return jsonify([
        {
            "id": topic.marks_topic_id,
            "name": f"{topic.marks_topic_name} ({topic.full_marks})"
        }
        for topic in topics
    ])