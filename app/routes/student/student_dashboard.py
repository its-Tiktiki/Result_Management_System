from flask import (
    Blueprint,
    render_template,
    session,
    redirect,
    url_for,
    flash
)

from app.models.teacher import AddStudentInfo
from app.routes.student.auth_check import student_roll_check

student_dashboard_bp = Blueprint(
    "student_dashboard",
    __name__,
    url_prefix="/student_dashboard"
)


@student_dashboard_bp.route("/")
def student_dashboard():

    # Student login check
    student_roll_check()

    student_roll = session.get("student_roll")

    if not student_roll:
        flash("Please login first.", "danger")
        return redirect(url_for("home.home"))

    # Get latest semester data
    student_data = (
        AddStudentInfo.query
        .filter_by(student_roll=student_roll)
        .order_by(
            AddStudentInfo.semester.desc(),
            AddStudentInfo.student_id.desc()
        )
        .first()
    )

    if not student_data:
        flash("Student information not found.", "danger")
        return redirect(url_for("home.home"))

    return render_template(
        "student/student_dashboard.html",
        student_data=student_data
    )