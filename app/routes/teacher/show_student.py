from flask import Blueprint, render_template, session, redirect, url_for
from app.models.teacher import AddStudentInfo
from app.models.assign import Department
from app.utils.add_student_form import SelectSemesterAndDepartmentForm

show_student_bp = Blueprint(
    "show_student",
    __name__,
    url_prefix="/show_student"
)


@show_student_bp.route("/", methods=["GET", "POST"])
def show_student():

    if not session.get("teacher"):
        return redirect(url_for("login.login"))

    form = SelectSemesterAndDepartmentForm()

    teacher_id = session.get("teacher_id")
    principal_id = session.get("temp_principal_id")   

    departments = Department.query.filter_by(
        principal_id=principal_id
    ).all()

    form.department_id.choices = [
        (d.department_id, f"{d.department_code} - {d.department_name}")
        for d in departments
    ]

    students = AddStudentInfo.query.filter_by(
        teacher_id=teacher_id
    ).all()


    form.sessions.choices = [
        (s, s)
        for s in sorted({
            x.sessions
            for x in students
                if x.sessions
        })
    ]

    form.semester.choices = [
        (s, f"Semester {s}")
        for s in sorted({x.semester for x in students})
    ]

    form.group.choices = [
        (g, g)
        for g in sorted({x.group for x in students if x.group})
    ]

    student_data = []

    if form.validate_on_submit():

        student_data = AddStudentInfo.query.filter_by(
            teacher_id=teacher_id,
            department_id=form.department_id.data,
            sessions = form.sessions.data,
            semester=form.semester.data,
            group=form.group.data
        ).all()

    return render_template(
        "teacher/load_student.html",
        form=form,
        student_data=student_data
    )