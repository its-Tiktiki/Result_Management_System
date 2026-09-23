from flask import Blueprint, redirect, url_for, render_template, session

from app.models.teacher import AddStudentInfo, AddMarks


view_student_details_bp = Blueprint(
    "view_student_details",
    __name__,
    url_prefix="/view_student_details"
)


@view_student_details_bp.route("/teacher<int:student_id>")
def view_student_details(student_id):

    if not session.get("teacher"):
        return redirect(url_for("login.login"))

    student = AddStudentInfo.query.get_or_404(student_id)

    marks = (
        AddMarks.query
        .filter_by(student_id=student.student_id)
        .all()
    )

    # Group marks by subject
    subjects = {}

    for mark in marks:

        subject_id = mark.subject.subject_id

        if subject_id not in subjects:
            subjects[subject_id] = {
                "subject": mark.subject,
                "marks": []
            }

        subjects[subject_id]["marks"].append(mark)

    return render_template(
        "teacher/get_marks_system/view_details.html",
        student=student,
        subjects=subjects.values()
    )

