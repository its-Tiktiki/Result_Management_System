from flask import (
    Blueprint,
    render_template,
    session,
    request
)

from sqlalchemy import func

from app.routes.student.auth_check import student_roll_check
from app.models.teacher import Attendance, AddStudentInfo
from app.models.assign import Subjects, Curriculum
from app.extensions import db

student_attendance_bp = Blueprint(
    "student_attendance",
    __name__,
    url_prefix="/student_attendance"
)

# ============================================================
# Student Attendance
# ============================================================

@student_attendance_bp.route("/")
def attendance():

    # --------------------------------------------------------
    # Student Authentication
    # --------------------------------------------------------

    student_roll_check()

    student_roll = session.get("student_roll")

    if not student_roll:
        return render_template(
            "student/attendance.html",
            attendance=None,
            subjects=[],
            selected_subject_id=None,
            total_class=0,
            total_present=0,
            total_absent=0,
            percentage=0
        )

    # ========================================================
    # Get ALL Student Records
    # ========================================================

    student_records = (
        AddStudentInfo.query
        .filter_by(student_roll=student_roll)
        .order_by(AddStudentInfo.semester.asc())
        .all()
    )

    if not student_records:
        return render_template(
            "student/attendance.html",
            attendance=None,
            subjects=[],
            selected_subject_id=None,
            total_class=0,
            total_present=0,
            total_absent=0,
            percentage=0
        )

    student_ids = [
        student.student_id
        for student in student_records
    ]

    # ========================================================
    # Get ALL Subjects Where Student Has Attendance
    # ========================================================

    attendance_subjects = (
        db.session.query(Subjects)
        .join(
            Attendance,
            Attendance.subject_id == Subjects.subject_id
        )
        .filter(
            Attendance.student_id.in_(student_ids)
        )
        .distinct()
        .all()
    )

    # ========================================================
    # Selected Subject
    # ========================================================

    selected_subject_id = request.args.get(
        "subject_id",
        type=int
    )

    page = request.args.get(
        "page",
        1,
        type=int
    )

    attendance = None

    total_class = 0
    total_present = 0
    total_absent = 0
    percentage = 0

    # ========================================================
    # If Subject Selected
    # ========================================================

    if selected_subject_id:

        # ----------------------------------------------------
        # Security Check
        # Subject must belong to student's attendance history
        # ----------------------------------------------------

        valid_subject = (
            db.session.query(Attendance)
            .filter(
                Attendance.student_id.in_(student_ids),
                Attendance.subject_id == selected_subject_id
            )
            .first()
        )

        if valid_subject:

            # =================================================
            # Attendance Records
            # =================================================

            attendance = (
                Attendance.query
                .filter(
                    Attendance.student_id.in_(student_ids),
                    Attendance.subject_id == selected_subject_id
                )
                .order_by(
                    Attendance.attendance_date.desc()
                )
                .paginate(
                    page=page,
                    per_page=15,
                    error_out=False
                )
            )

            # =================================================
            # Total Class
            # =================================================

            total_class = (
                db.session.query(
                    func.count(Attendance.attendance_id)
                )
                .filter(
                    Attendance.student_id.in_(student_ids),
                    Attendance.subject_id == selected_subject_id
                )
                .scalar()
            ) or 0

            # =================================================
            # Total Present
            # =================================================

            total_present = (
                db.session.query(
                    func.count(Attendance.attendance_id)
                )
                .filter(
                    Attendance.student_id.in_(student_ids),
                    Attendance.subject_id == selected_subject_id,
                    Attendance.status == "P"
                )
                .scalar()
            ) or 0

            # =================================================
            # Total Absent
            # =================================================

            total_absent = (
                db.session.query(
                    func.count(Attendance.attendance_id)
                )
                .filter(
                    Attendance.student_id.in_(student_ids),
                    Attendance.subject_id == selected_subject_id,
                    Attendance.status == "A"
                )
                .scalar()
            ) or 0

            # =================================================
            # Attendance Percentage
            # =================================================

            if total_class > 0:
                percentage = round(
                    (total_present / total_class) * 100,
                    2
                )

        else:
            selected_subject_id = None

    # ========================================================
    # Render
    # ========================================================

    return render_template(
        "student/attendance.html",
        attendance=attendance,
        subjects=attendance_subjects,
        selected_subject_id=selected_subject_id,
        total_class=total_class,
        total_present=total_present,
        total_absent=total_absent,
        percentage=percentage
    )