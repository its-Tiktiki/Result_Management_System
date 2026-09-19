from flask import jsonify,Blueprint
from app.models.teacher import Attendance

attendance_api_bp = Blueprint(
    "attendance_api",
    __name__,
    url_prefix="/attendance/api/"
)

@attendance_api_bp.route("/",methods=["GET"])
def attendance_api():
    student_data = Attendance.query.all()

    data = []

    for student in student_data:
        data.append({
            "attendance_id": student.attendance_id,
            "student_id": student.student_id,
            "student_roll": student.student.student_roll,
            "subject_name": student.subject.subject_name,
            "attendance_date": student.attendance_date.isoformat(),
            "status": student.status,  
        })

    return jsonify({
        "success": True,
        "total": len(data),
        "data": data,
    })
