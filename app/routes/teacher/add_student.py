from flask import Blueprint, session, redirect, url_for, render_template, flash
from app.utils.add_student_form import AddStudentForm
from app.models.teacher import AddStudentInfo
from app.models.assign import Department
from app.models.assign import TeacherAssignment
from app.extensions import db

add_student_bp = Blueprint("add_student", __name__, url_prefix="/add_student")


@add_student_bp.route("/", methods=["GET", "POST"])
def add_student():

    if not session.get("teacher"):
        return redirect(url_for("login.login"))

    teacher_id = session.get("teacher_id")
    principal_id = session.get("temp_principal_id")

    student_form = AddStudentForm()

    # ==========================
    # Teacher Assignments
    # ==========================

    assignments = TeacherAssignment.query.filter_by(teacher_id=teacher_id).all()

    # ==========================
    # Department List
    # ==========================

    department_ids = list({assignment.department_id for assignment in assignments})

    departments = Department.query.filter(
        Department.principal_id == principal_id,
        Department.department_id.in_(department_ids),
    ).all()

    student_form.department_id.choices = [
        (
            department.department_id,
            f"{department.department_code} - {department.department_name}",
        )
        for department in departments
    ]

    # ==========================
    # Semester List
    # ==========================

    semesters = sorted({assignment.semester for assignment in assignments})
    student_form.semester.choices = [
        (semester, f"Semester {semester}") for semester in semesters
    ]

    # ==========================
    # Add Student
    # ==========================

    try:

        if student_form.validate_on_submit():

            student = AddStudentInfo(
                student_roll=student_form.student_roll.data,
                student_full_name=student_form.student_full_name.data,
                semester=student_form.semester.data,
                sessions=student_form.sessions.data,
                group=student_form.group.data,
                department_id=student_form.department_id.data,
                teacher_id=teacher_id,
                principal_id=principal_id,
            )

            db.session.add(student)
            db.session.commit()

            flash("Student added successfully", "success")

            return redirect(url_for("teacher_dashboard.teacher_dashboard"))

    except Exception:
        db.session.rollback()
        flash("Something went wrong", "danger")

    return render_template("teacher/add_student.html", student_form=student_form)
