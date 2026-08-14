from flask import Blueprint,jsonify,request
from app.extensions import db
from app.models.teacher import AddStudentInfo

student_data_api = Blueprint(
    "student_api",
    __name__,
    url_prefix="/api/students"
)

@student_data_api.route("/",methods=["GET"])
def get_students():
    students = AddStudentInfo.query.all()
    data = []

    for student in students:
        data.append({
            "student_id": student.student_id,
            "roll": student.student_roll,
            "name": student.student_full_name,
            "semester": student.semester,
            "group": student.group,
            "cgpa": student.cgpa,
            "department_id": student.department_id,
            "principal_id": student.principal_id,
            "teacher_id": student.teacher_id
        })
    return jsonify({
        "success" : True,
        "count" : len(data),
        "students" : data
    }), 200

@student_data_api.route("/<int:student_id>", methods=["GET"])
def get_student(student_id):
    student = AddStudentInfo.query.get(student_id)

    if not student:
        return jsonify({
            "success": False,
            "message": "Student not found"
        }), 404

    return jsonify({
        "success": True,
        "student": {
            "student_id": student.student_id,
            "roll": student.student_roll,
            "name": student.student_full_name,
            "semester": student.semester,
            "group": student.group,
            "cgpa": student.cgpa,
            "department_id": student.department_id,
            "principal_id": student.principal_id,
            "teacher_id": student.teacher_id
        }
    }), 200


@student_data_api.route("/roll/<int:roll>", methods=["GET"])
def get_student_by_roll(roll):
    student = AddStudentInfo.query.filter_by(
        student_roll=roll
    ).first()
    if not student:
        return jsonify({
            "success": False,
            "message": "Student not found"
        }), 404
    return jsonify({
        "success": True,
        "student": {
            "student_id": student.student_id,
            "roll": student.student_roll,
            "name": student.student_full_name,
            "semester": student.semester,
            "group": student.group,
            "cgpa": student.cgpa,
            "department_id": student.department_id,
            "principal_id": student.principal_id,
            "teacher_id": student.teacher_id
        }
    }), 200