from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from app.extensions import db
from app.models.assign import Subjects, TeacherAssignment
from app.models.teacher import AddMarks, AddStudentInfo, MarksTopic
from app.utils.add_marks_form import AddMarksForm

add_marks_bp = Blueprint("add_marks", __name__, url_prefix="/add_marks")


@add_marks_bp.route("/teacher/<int:student_id>", methods=["GET", "POST"])
def add_marks(student_id):
    if not session.get("teacher"):
        return redirect(url_for("login.login"))

    teacher_id = session.get("teacher_id")
    student = AddStudentInfo.query.get_or_404(student_id)
    form = AddMarksForm()

    # ==========================
    # Subject Dropdown
    # ==========================
    subjects = (
        db.session.query(Subjects)
        .join(
            TeacherAssignment,
            TeacherAssignment.subject_id == Subjects.subject_id,
        )
        .filter(TeacherAssignment.teacher_id == teacher_id)
        .distinct()
        .all()
    )
    form.subject.choices = [(0, "Select Subject")] + [
        (s.subject_id, f"{s.subject_code} - {s.subject_name}")
        for s in subjects
    ]

    if form.subject.data:
        topics = MarksTopic.query.filter_by(
            teacher_id=teacher_id, subject_id=form.subject.data
        ).all()
        form.marks_topic.choices = [
            (t.marks_topic_id, f"{t.marks_topic_name} ({t.full_marks})")
            for t in topics
        ]
    else:
        form.marks_topic.choices = []

    if form.validate_on_submit():
        existing = AddMarks.query.filter_by(
            student_id=student.student_id,
            subject_id=form.subject.data,
            marks_topic_id=form.marks_topic.data,
        ).first()

        if existing:
            flash("Marks already exists.", "warning")
            return redirect(
                url_for("add_marks.add_marks", student_id=student.student_id)
            )

        mark = AddMarks(
            student_id=student.student_id,
            subject_id=form.subject.data,
            teacher_id=teacher_id,
            marks_topic_id=form.marks_topic.data,
            obtained_marks=form.get_marks.data,
        )

        db.session.add(mark)
        db.session.commit()

        flash("Marks Added Successfully", "success")
        return redirect(url_for("get_marks.show_student"))

    return render_template(
        "teacher/get_marks_system/add_marks.html", form=form, student=student
    )


@add_marks_bp.route("/teacher/edit/<int:marks_id>", methods=["GET", "POST"])
def edit_marks(marks_id):
    if not session.get("teacher"):
        return redirect(url_for("login.login"))

    teacher_id = session.get("teacher_id")

    mark = AddMarks.query.get_or_404(marks_id)

    if mark.teacher_id != teacher_id:
        flash("You are not authorized to edit this mark.", "danger")
        return redirect(url_for("get_marks.show_student"))

    form = AddMarksForm()

    # ==========================
    # Subject Dropdown
    # ==========================
    subjects = (
        db.session.query(Subjects)
        .join(
            TeacherAssignment,
            TeacherAssignment.subject_id == Subjects.subject_id,
        )
        .filter(TeacherAssignment.teacher_id == teacher_id)
        .distinct()
        .all()
    )

    form.subject.choices = [(0, "Select Subject")] + [
        (s.subject_id, f"{s.subject_code} - {s.subject_name}")
        for s in subjects
    ]

    # ==========================
    # Set Subject
    # ==========================
    if request.method == "GET":
        form.subject.data = mark.subject_id

    # ==========================
    # Marks Topic Dropdown
    # ==========================
    if form.subject.data:
        topics = MarksTopic.query.filter_by(
            teacher_id=teacher_id, subject_id=form.subject.data
        ).all()

        form.marks_topic.choices = [
            (t.marks_topic_id, f"{t.marks_topic_name} ({t.full_marks})")
            for t in topics
        ]
    else:
        form.marks_topic.choices = []

    # ==========================
    # GET → Existing Marks
    # ==========================
    if request.method == "GET":
        form.marks_topic.data = mark.marks_topic_id
        form.get_marks.data = mark.obtained_marks

    # ==========================
    # POST → Update
    # ==========================
    if form.validate_on_submit():
        existing = AddMarks.query.filter(
            AddMarks.student_id == mark.student_id,
            AddMarks.subject_id == form.subject.data,
            AddMarks.marks_topic_id == form.marks_topic.data,
            AddMarks.marks_id != mark.marks_id,
        ).first()

        if existing:
            flash(
                "Marks already exists for this subject and topic.",
                "warning",
            )
            return redirect(
                url_for("add_marks.edit_marks", marks_id=mark.marks_id)
            )

        mark.subject_id = form.subject.data
        mark.marks_topic_id = form.marks_topic.data
        mark.obtained_marks = form.get_marks.data

        db.session.commit()

        flash("Marks Updated Successfully", "success")

        return redirect(url_for("get_marks.show_student"))

    return render_template(
        "teacher/get_marks_system/add_marks.html",
        form=form,
        student=mark.student,
        edit_mode=True,
        mark=mark,
    )