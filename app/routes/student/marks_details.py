from flask import Blueprint, render_template, session
from sqlalchemy import func
from app.routes.student.auth_check import student_roll_check
from app.models.teacher import AddMarks, MarksTopic, AddStudentInfo
from app.models.assign import Subjects
from app.extensions import db


subjects_marks_bp = Blueprint(
    "subjects_marks",
    __name__,
    url_prefix="/subjects_marks"
)


@subjects_marks_bp.route("/")
def subjects_marks():

    student_roll_check()

    student_roll = session.get("student_roll")

    # ========================================================
    # Get ALL student records
    # ========================================================

    student_records = (
        AddStudentInfo.query
        .filter_by(student_roll=student_roll)
        .all()
    )

    student_ids = [
        student.student_id
        for student in student_records
    ]

    # ========================================================
    # Get ALL subjects with marks
    # ========================================================

    subjects_marks = (
        db.session.query(
            Subjects.subject_id,
            Subjects.subject_code,
            Subjects.subject_name,
            func.sum(AddMarks.obtained_marks).label("total_marks")
        )
        .join(
            AddMarks,
            AddMarks.subject_id == Subjects.subject_id
        )
        .filter(
            AddMarks.student_id.in_(student_ids)
        )
        .group_by(
            Subjects.subject_id,
            Subjects.subject_code,
            Subjects.subject_name
        )
        .all()
    )

    return render_template(
        "student/subjects_marks_details.html",
        subjects_marks=subjects_marks
    )


@subjects_marks_bp.route("/details/<int:subject_id>")
def subject_details(subject_id):

    student_roll_check()

    student_roll = session.get("student_roll")

    # ========================================================
    # Get ALL student records
    # ========================================================

    student_records = (
        AddStudentInfo.query
        .filter_by(student_roll=student_roll)
        .all()
    )

    student_ids = [
        student.student_id
        for student in student_records
    ]

    # ========================================================
    # Subject
    # ========================================================

    subject = Subjects.query.get_or_404(subject_id)

    # ========================================================
    # Get marks from ALL semesters
    # ========================================================

    marks = (
        AddMarks.query
        .filter(
            AddMarks.student_id.in_(student_ids),
            AddMarks.subject_id == subject_id
        )
        .all()
    )

    # ========================================================
    # Total marks
    # ========================================================

    total = (
        db.session.query(
            func.sum(MarksTopic.full_marks).label("full"),
            func.sum(AddMarks.obtained_marks).label("obtained")
        )
        .join(
            MarksTopic,
            MarksTopic.marks_topic_id == AddMarks.marks_topic_id
        )
        .filter(
            AddMarks.student_id.in_(student_ids),
            AddMarks.subject_id == subject_id
        )
        .first()
    )

    return render_template(
        "student/subject_details.html",
        subject=subject,
        marks=marks,
        total=total
    )