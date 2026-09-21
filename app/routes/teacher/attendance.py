from flask import Blueprint, render_template, session, redirect, url_for, flash, request
from app.extensions import db
from app.models.assign import Department, TeacherAssignment
from app.models.teacher import AddStudentInfo, Attendance
from app.utils.attendance_form import AttendanceForm
from datetime import datetime


attendance_bp = Blueprint("attendence", __name__, url_prefix="/attendance")


@attendance_bp.route("/", methods=["GET", "POST"])
def attendance():

    if not session.get("teacher"):
        return redirect(url_for("login.login"))

    teacher_id = session.get("teacher_id")
    principal_id = session.get("temp_principal_id")

    form = AttendanceForm()

    student_data = []
    saved_attendance = {}

    try:

        assignments = TeacherAssignment.query.filter_by(
            teacher_id=teacher_id
        ).all()

        if not assignments:
            flash("You have no assigned subjects.", "warning")

            return render_template(
                "teacher/attendance.html",
                form=form,
                students=[],
                saved_attendance={}
            )

        # --------------------------------------------------
        # Department choices
        # --------------------------------------------------

        assigned_department_ids = {
            assignment.department_id
            for assignment in assignments
            if assignment.department_id is not None
        }

        departments = Department.query.filter(
            Department.principal_id == principal_id,
            Department.department_id.in_(assigned_department_ids)
        ).all()

        form.department_id.choices = [
            (
                department.department_id,
                f"{department.department_code} - {department.department_name}"
            )
            for department in departments
        ]

        # --------------------------------------------------
        # Semester choices
        # --------------------------------------------------

        assigned_semesters = sorted({
            assignment.semester
            for assignment in assignments
            if assignment.semester is not None
        })

        form.semester.choices = [
            (semester, f"Semester {semester}")
            for semester in assigned_semesters
        ]

        # --------------------------------------------------
        # Selected values
        # --------------------------------------------------

        selected_department_id = None
        selected_semester = None
        selected_sessions = None
        selected_group = None

        if request.method == "POST":

            department_value = request.form.get("department_id")
            semester_value = request.form.get("semester")
            sessions_value = request.form.get("sessions")
            group_value = request.form.get("group")

            if department_value:
                selected_department_id = int(department_value)

            if semester_value:
                selected_semester = int(semester_value)

            if sessions_value:
                selected_sessions = sessions_value

            if group_value:
                selected_group = group_value

        # --------------------------------------------------
        # Student query
        # Teacher's students only
        # --------------------------------------------------

        assigned_students_query = AddStudentInfo.query.filter_by(
            teacher_id=teacher_id
        )

        # Department filter
        if selected_department_id is not None:
            assigned_students_query = assigned_students_query.filter_by(
                department_id=selected_department_id
            )

        # Semester filter
        if selected_semester is not None:
            assigned_students_query = assigned_students_query.filter_by(
                semester=selected_semester
            )

        # IMPORTANT:
        # Do NOT apply sessions/group filter here yet.
        #
        # Because we need all available sessions and groups
        # for the selected department + semester.

        assigned_students = assigned_students_query.all()

        # --------------------------------------------------
        # Sessions choices
        # Based on Department + Semester
        # --------------------------------------------------

        session_values = sorted({
            student.sessions
            for student in assigned_students
            if student.sessions
        })

        form.sessions.choices = [
            (sessions, sessions)
            for sessions in session_values
        ]

        # --------------------------------------------------
        # Group choices
        # Also based on Department + Semester
        #
        # Do NOT filter by selected_sessions here.
        # Otherwise old groups disappear.
        # --------------------------------------------------

        group_values = sorted({
            student.group
            for student in assigned_students
            if student.group
        })

        form.group.choices = [
            (group, group)
            for group in group_values
        ]

        # --------------------------------------------------
        # Subject choices
        # Based on Teacher Assignment
        # --------------------------------------------------

        subject_assignments = TeacherAssignment.query.filter_by(
            teacher_id=teacher_id
        )

        if selected_department_id is not None:
            subject_assignments = subject_assignments.filter_by(
                department_id=selected_department_id
            )

        if selected_semester is not None:
            subject_assignments = subject_assignments.filter_by(
                semester=selected_semester
            )

        subject_assignments = subject_assignments.all()

        form.subject_id.choices = [
            (
                assignment.subject_id,
                f"{assignment.subject.subject_code} - "
                f"{assignment.subject.subject_name}"
            )
            for assignment in subject_assignments
            if assignment.subject
        ]

        # --------------------------------------------------
        # Now filter students by Sessions + Group
        #
        # This happens AFTER choices are created.
        # --------------------------------------------------

        filtered_students = assigned_students

        if selected_sessions is not None:
            filtered_students = [
                student
                for student in filtered_students
                if student.sessions == selected_sessions
            ]

        if selected_group is not None:
            filtered_students = [
                student
                for student in filtered_students
                if student.group == selected_group
            ]

        # --------------------------------------------------
        # Validate form
        # --------------------------------------------------

        if form.validate_on_submit():

            selected_department_id = form.department_id.data
            selected_semester = form.semester.data
            selected_sessions = form.sessions.data
            selected_subject_id = form.subject_id.data
            selected_group = form.group.data
            selected_date = form.attendance_date.data

            # --------------------------------------------------
            # Check teacher assignment
            # --------------------------------------------------

            assignment = TeacherAssignment.query.filter_by(
                teacher_id=teacher_id,
                department_id=selected_department_id,
                semester=selected_semester,
                subject_id=selected_subject_id
            ).first()

            if not assignment:

                flash(
                    "You are not assigned to this subject.",
                    "danger"
                )

                return render_template(
                    "teacher/attendance.html",
                    form=form,
                    students=[],
                    saved_attendance={}
                )

            # --------------------------------------------------
            # Get students
            #
            # Teacher ID is ALWAYS included here.
            # Subject only determines attendance subject.
            # --------------------------------------------------

            student_query = AddStudentInfo.query.filter_by(
                teacher_id=teacher_id,
                department_id=selected_department_id,
                semester=selected_semester,
                sessions=selected_sessions,
                group=selected_group
            )

            student_data = student_query.order_by(
                AddStudentInfo.student_roll
            ).all()

            # --------------------------------------------------
            # Get existing attendance
            # --------------------------------------------------

            if student_data:

                student_ids = [
                    student.student_id
                    for student in student_data
                ]

                attendance_records = Attendance.query.filter(
                    Attendance.attendance_date == selected_date,
                    Attendance.subject_id == selected_subject_id,
                    Attendance.student_id.in_(student_ids)
                ).all()

                saved_attendance = {
                    record.student_id: record.status
                    for record in attendance_records
                }

    except Exception as e:

        db.session.rollback()

        print("Attendance Error:", repr(e))

        flash(
            "Something went wrong while loading attendance.",
            "danger"
        )

    return render_template(
        "teacher/attendance.html",
        form=form,
        students=student_data,
        saved_attendance=saved_attendance
    )
# ============================================================
# Save Attendance
# ============================================================

@attendance_bp.route("/save", methods=["POST"])
def save_attendance():
    if not session.get("teacher"):
        return redirect(url_for("login.login"))

    teacher_id = session.get("teacher_id")

    try:
        attendance_date_string = request.form.get("attendance_date")
        department_id_string = request.form.get("department_id")
        semester_string = request.form.get("semester")
        subject_id_string = request.form.get("subject_id")
        group = request.form.get("group")

        if not attendance_date_string:
            flash("Attendance date is required.", "danger")
            return redirect(url_for("attendence.attendance"))

        if not department_id_string:
            flash("Department is required.", "danger")
            return redirect(url_for("attendence.attendance"))

        if not semester_string:
            flash("Semester is required.", "danger")
            return redirect(url_for("attendence.attendance"))

        if not subject_id_string:
            flash("Subject is required.", "danger")
            return redirect(url_for("attendence.attendance"))

        if not group:
            flash("Group is required.", "danger")
            return redirect(url_for("attendence.attendance"))

        attendance_date = datetime.strptime(attendance_date_string, "%Y-%m-%d").date()
        department_id = int(department_id_string)
        semester = int(semester_string)
        subject_id = int(subject_id_string)

        assignment = TeacherAssignment.query.filter_by(teacher_id=teacher_id, department_id=department_id, semester=semester, subject_id=subject_id).first()

        if not assignment:
            flash("You are not assigned to this subject.", "danger")
            return redirect(url_for("attendence.attendance"))

        students = AddStudentInfo.query.filter_by(teacher_id=teacher_id, department_id=department_id, semester=semester, group=group).order_by(AddStudentInfo.student_roll).all()

        if not students:
            flash("No students found for the selected class.", "warning")
            return redirect(url_for("attendence.attendance"))

        saved_count = 0
        updated_count = 0

        for student in students:
            status = request.form.get(f"attendance_{student.student_id}")

            if not status or status not in ("P", "A"):
                continue

            old_attendance = Attendance.query.filter_by(student_id=student.student_id, subject_id=subject_id, attendance_date=attendance_date).first()

            if old_attendance:
                old_attendance.status = status
                old_attendance.teacher_id = teacher_id
                updated_count += 1
            else:
                attendance = Attendance(student_id=student.student_id, teacher_id=teacher_id, subject_id=subject_id, attendance_date=attendance_date, status=status)
                db.session.add(attendance)
                saved_count += 1

        db.session.commit()
        flash(f"Attendance saved successfully. New: {saved_count}, Updated: {updated_count}", "success")

    except ValueError:
        db.session.rollback()
        flash("Invalid attendance data.", "danger")

    except IntegrityError as e:
        db.session.rollback()
        print("Attendance Integrity Error:", repr(e))
        flash("Attendance could not be saved because of a database constraint. Check the attendance table structure.", "danger")

    except Exception as e:
        db.session.rollback()
        print("Save Attendance Error:", repr(e))
        flash("Something went wrong while saving attendance.", "danger")

    return redirect(url_for("attendence.attendance"))