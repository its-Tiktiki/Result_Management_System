from flask import Blueprint, render_template, session, redirect, url_for, flash,request
from app.models.teacher import AddStudentInfo,MarksTopic,AddMarks
from app.models.assign import Department,Subjects,TeacherAssignment
from app.utils.add_student_form import SelectSemesterAndDepartmentForm
from app.utils.marks_forms import MarksTopicForm
from app.extensions import db


get_marks_bp = Blueprint(
    "get_marks",
    __name__,
    url_prefix="/get_marks"
)

@get_marks_bp.route("/", methods=["GET", "POST"])
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

    form.semester.choices = [
        (s, f"Semester {s}")
        for s in sorted({x.semester for x in students})
    ]

    form.group.choices = [
        (g, g)
        for g in sorted({x.group for x in students if x.group})
    ]


    form.sessions.choices = [
        (s, s)
        for s in sorted({
            x.sessions
            for x in students
                if x.sessions
        })
    ]

    student_data = []

    if form.validate_on_submit():

        student_data = AddStudentInfo.query.filter_by(
            teacher_id=teacher_id,
            department_id=form.department_id.data,
            semester=form.semester.data,
            sessions=form.sessions.data,
            group=form.group.data
        ).all()

    return render_template(
        "teacher/get_marks_system/get_marks_views.html",
        form=form,
        student_data=student_data
    )

@get_marks_bp.route("/add_marks_topic", methods=["GET", "POST"])
def get_marks_topic_name():
    if not session.get("teacher"):
        return redirect(url_for("login.login"))

    form = MarksTopicForm()

    teacher_id = session.get("teacher_id")

    # ==========================
    # Subject List
    # ==========================
    subjects = (
        db.session.query(Subjects)
        .join(
            TeacherAssignment,
            TeacherAssignment.subject_id == Subjects.subject_id
        )
        .filter(
            TeacherAssignment.teacher_id == teacher_id
        )
        .distinct()
        .all()
    )

    form.subject.choices = [
        (s.subject_id, f"{s.subject_code} - {s.subject_name}")
        for s in subjects
    ]

    # ==========================
    # Department List
    # ==========================
    departments = (
        db.session.query(Department)
        .join(
            TeacherAssignment,
            TeacherAssignment.department_id == Department.department_id
        )
        .filter(
            TeacherAssignment.teacher_id == teacher_id
        )
        .distinct()
        .all()
    )

    form.department_id.choices = [
        (d.department_id, f"{d.department_code} - {d.department_name}")
        for d in departments
    ]

    # ==========================
    # Save Marks Topic
    # ==========================
    if form.validate_on_submit():

        marks_topic = MarksTopic(
            marks_topic_name=form.add_marks_topic_name.data,
            full_marks=form.full_marks.data,
            subject_id=form.subject.data,
            teacher_id=teacher_id
        )

        db.session.add(marks_topic)
        db.session.commit()

        flash("Marks topic added successfully", "success")
        return redirect(url_for("get_marks.get_marks_topic_name"))

    return render_template(
        "teacher/get_marks_system/add_marks_topic.html",
        form=form
    )

@get_marks_bp.route("/show_marks_system")
def show_marks_system():
    if not session.get("teacher"):
        return redirect(url_for("login.login"))
    
    teacher_id = session.get("teacher_id")
    marks_topic_name = MarksTopic.query.filter_by(
        teacher_id=teacher_id
    ).all()

    return render_template(
        "teacher/get_marks_system/show_marks_system.html",
        marks_topic_name=marks_topic_name
    )

@get_marks_bp.route("/teacher/<int:marks_topic_id>/edit", methods=["GET", "POST"])
def edit_mark_topic(marks_topic_id):

    if not session.get("teacher"):
        return redirect(url_for("login.login"))

    teacher_id = session.get("teacher_id")

    topic = MarksTopic.query.get_or_404(marks_topic_id)

    form = MarksTopicForm()

    # -----------------------------
    # Department Dropdown
    # -----------------------------
    departments = (
        db.session.query(Department)
        .join(
            TeacherAssignment,
            TeacherAssignment.department_id == Department.department_id
        )
        .filter(
            TeacherAssignment.teacher_id == teacher_id
        )
        .distinct()
        .all()
    )

    form.department_id.choices = [
        (
            str(d.department_id),
            d.department_name
        )
        for d in departments
    ]

    # -----------------------------
    # Subject Dropdown
    # -----------------------------
    subjects = (
        db.session.query(Subjects)
        .join(
            TeacherAssignment,
            TeacherAssignment.subject_id == Subjects.subject_id
        )
        .filter(
            TeacherAssignment.teacher_id == teacher_id
        )
        .distinct()
        .all()
    )

    form.subject.choices = [
        (
            str(s.subject_id),
            f"{s.subject_code} - {s.subject_name}"
        )
        for s in subjects
    ]

    # -----------------------------
    # First Load
    # -----------------------------
    if request.method == "GET":

        assignment = TeacherAssignment.query.filter_by(
            teacher_id=teacher_id,
            subject_id=topic.subject_id
        ).first()

        if assignment:
            form.department_id.data = str(assignment.department_id)

        form.subject.data = str(topic.subject_id)
        form.add_marks_topic_name.data = topic.marks_topic_name
        form.full_marks.data = topic.full_marks

    # -----------------------------
    # Update
    # -----------------------------
    if form.validate_on_submit():

        duplicate = MarksTopic.query.filter(
            MarksTopic.teacher_id == teacher_id,
            MarksTopic.subject_id == int(form.subject.data),
            MarksTopic.marks_topic_name == form.add_marks_topic_name.data,
            MarksTopic.marks_topic_id != marks_topic_id
        ).first()

        if duplicate:

            flash(
                "Marks Topic already exists.",
                "warning"
            )

            return redirect(
                url_for(
                    "get_marks.edit_mark_topic",
                    marks_topic_id=marks_topic_id
                )
            )

        topic.subject_id = int(form.subject.data)
        topic.marks_topic_name = form.add_marks_topic_name.data
        topic.full_marks = form.full_marks.data

        try:

            db.session.commit()

            flash(
                "Marks Topic Updated Successfully",
                "success"
            )

            return redirect(
                url_for("get_marks.show_marks_system")
            )

        except Exception as e:

            db.session.rollback()

            flash(
                f"Error : {str(e)}",
                "danger"
            )

    return render_template(
        "teacher/get_marks_system/edit_mark_topic.html",
        form=form,
        marks_topic_name=topic
    )

@get_marks_bp.route("/teacher/<int:marks_topic_id>/delete", methods=["POST"])
def delete_mark_topic(marks_topic_id):

    if not session.get("teacher"):
        return redirect(url_for("login.login"))

    topic = MarksTopic.query.get_or_404(marks_topic_id)

    if AddMarks.query.filter_by(marks_topic_id=marks_topic_id).first():
        flash(
            "This marks topic is already used. You can't delete it.",
            "warning"
        )
        return redirect(url_for("get_marks.show_marks_system"))

    db.session.delete(topic)
    db.session.commit()

    flash("Deleted Successfully", "success")

    return redirect(url_for("get_marks.show_marks_system"))