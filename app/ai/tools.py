"""
Agent tool functions for the Mistral-powered assistant.

Each function here is meant to eventually be exposed to the model as a
"tool" (function calling). For now they are plain Python functions we can
call and test directly before wiring up tool-call routing.

Convention used across these tools:
- Every function is scoped by teacher_id, matching the ownership pattern
  already used in app/routes/teacher/show_student.py (AddStudentInfo is
  queried by teacher_id, not principal_id).
- Every function returns a plain dict (JSON-serializable) or None if not
  found / not owned by this teacher. Never return raw SQLAlchemy model
  instances to the agent layer.
"""

from app.models.teacher import AddStudentInfo, Attendance, AddMarks
from app.models.assign import Department, Subjects


def get_student_data(student_id, teacher_id):
    """
    Fetch a single student's profile by internal student_id,
    scoped to the requesting teacher.

    Args:
        student_id (int): AddStudentInfo.student_id (auto-increment PK).
        teacher_id (int): The teacher making the request (from session).

    Returns:
        dict | None: Student data, or None if not found for this teacher.
    """
    student = AddStudentInfo.query.filter_by(
        student_id=student_id,
        teacher_id=teacher_id
    ).first()

    if student is None:
        return None

    department = Department.query.filter_by(
        department_id=student.department_id
    ).first()

    return {
        "student_id": student.student_id,
        "student_roll": student.student_roll,
        "student_full_name": student.student_full_name,
        "semester": student.semester,
        "group": student.group,
        "cgpa": student.cgpa,
        "department_id": student.department_id,
        "department_name": department.department_name if department else None,
        "department_code": department.department_code if department else None,
        "teacher_id": student.teacher_id,
        "principal_id": student.principal_id,
    }


def get_student_by_roll(student_roll, teacher_id):
    """
    Fetch a single student's profile by roll number (the human-facing ID),
    scoped to the requesting teacher.

    Args:
        student_roll (int): AddStudentInfo.student_roll (unique, user-facing).
        teacher_id (int): The teacher making the request (from session).

    Returns:
        dict | None: Student data, or None if not found for this teacher.
    """
    student = AddStudentInfo.query.filter_by(
        student_roll=student_roll,
        teacher_id=teacher_id
    ).first()

    if student is None:
        return None

    department = Department.query.filter_by(
        department_id=student.department_id
    ).first()

    return {
        "student_id": student.student_id,
        "student_roll": student.student_roll,
        "student_full_name": student.student_full_name,
        "semester": student.semester,
        "group": student.group,
        "cgpa": student.cgpa,
        "department_id": student.department_id,
        "department_name": department.department_name if department else None,
        "department_code": department.department_code if department else None,
        "teacher_id": student.teacher_id,
        "principal_id": student.principal_id,
    }


if __name__ == "__main__":
    # Manual test harness. Run with:
    #   python -m app.ai.tools
    # (Requires an app context and an existing student/teacher in the DB —
    # adjust the ids below to match real rows in your database.db)
    from app import create_app  # adjust import to match your actual app factory

    app = create_app()
    with app.app_context():
        result = get_student_data(student_id=1, teacher_id=1)
        print(result)