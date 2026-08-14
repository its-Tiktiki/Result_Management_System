# Database Structure Summary

Plain-language reference for the Result Management System's data model. Use this instead of re-pasting model files when building new features.

---

## Core entities and hierarchy

The system has a strict ownership chain:

```
Admin
  └── Principal (created by Admin)
        ├── Department (created by Principal)
        ├── Subjects (created by Principal)
        └── Teacher (created by Principal)
              └── Student (created by Teacher)
                    ├── Attendance (recorded by Teacher)
                    └── Marks (recorded by Teacher, via Marks Topics)
```

Almost every table carries a `principal_id` and/or `teacher_id` foreign key, so records are naturally scoped to "which school" and "which teacher" they belong to. Existing routes filter queries by `session["teacher_id"]` / `session["temp_principal_id"]` rather than relying on any global "current user" object — there's no Flask-Login style `current_user`, just raw session keys.

---

## Models

### Admin (`admin.py` → table `admin`)
The single hard-coded admin account.
- `id`, `username` (unique), `password` (plain text currently)

### PrincipalDataInfo (`admin.py` → table `principal_info`)
A principal (school-level account), created by Admin.
- `principal_id` (PK)
- `first_name`, `last_name`
- `mobile_number` (unique), `email` (unique)
- `institute` (unique), `institute_code` (unique) — identifies the school
- `username` (unique), `password`

### TeacherAddInfo (`principal.py` → table `teacher_info`)
A teacher account, created by a Principal.
- `teacher_id` (PK)
- `first_name`, `last_name`
- `institute`, `institute_code` (copied from principal at creation time)
- `phone` (unique), `email` (unique)
- `username` (unique), `password`
- `principal_id` → FK to `principal_info.principal_id`
- `shift` — "Morning" or "Day"

### Department (`assign.py` → table `departments`)
Created by a Principal.
- `department_id` (PK)
- `department_code` (integer), `department_name`
- `principal_id` → FK to `principal_info.principal_id`
- `teacher_id` → FK to `teacher_info.teacher_id` (nullable — a department can optionally be tied to a teacher)
- Unique constraint: `(principal_id, department_code)` — department codes are unique per school, not globally

### Subjects (`assign.py` → table `subjects`)
Created by a Principal.
- `subject_id` (PK)
- `subject_code` (string), `subject_name`
- `principal_id` → FK to `principal_info.principal_id`
- `student_id` → FK to `student_data.student_id` (nullable — unusual: a subject row can reference a single student; likely used for elective/optional subject assignment rather than a general subject catalog. Worth double-checking usage before building on this field.)
- `teacher_id` → FK to `teacher_info.teacher_id` (nullable)
- Unique constraint: `(principal_id, subject_code)`

### Curriculum (`assign.py` → table `curriculum`)
Joins Department + Semester + Subject — defines what subjects exist in which semester of which department.
- `curriculum_id` (PK)
- `department_id` → FK to `departments.department_id`
- `semester` (integer)
- `subject_id` → FK to `subjects.subject_id`
- Relationships: `subject` (→ Subjects), `department` (→ Department)

### TeacherAssignment (`assign.py` → table `teacher_assignments`)
Assigns a teacher to teach a specific subject, in a specific department, in a specific semester.
- `assignment_id` (PK)
- `teacher_id` → FK to `teacher_info.teacher_id`
- `department_id` → FK to `departments.department_id`
- `semester` (integer)
- `subject_id` → FK to `subjects.subject_id`
- `created_at` (datetime, defaults to UTC now)
- Relationships: `teacher` (→ TeacherAddInfo), `department` (→ Department), `subject` (→ Subjects)

### AddStudentInfo (`teacher.py` → table `student_data`)
A student, created by a Teacher.
- `student_id` (PK, autoincrement)
- `student_roll` (integer, unique)
- `student_full_name`
- `semester` (integer)
- `group` — single character (e.g. "A", "B")
- `cgpa` (float, default 0)
- `department_id` → FK to `departments.department_id`
- `principal_id` → FK to `principal_info.principal_id` (nullable)
- `teacher_id` → FK to `teacher_info.teacher_id` (nullable) — this is what scopes "my students" for a teacher

### Attendance (`teacher.py` → table `attendance`)
One row per student per day.
- `attendance_id` (PK, autoincrement)
- `student_id` → FK to `student_data.student_id`
- `teacher_id` → FK to `teacher_info.teacher_id`
- `attendance_date` (date)
- `status` — single character (e.g. "P"/"A"; exact convention not enforced in schema, check the form/route that writes it)
- `created_at` (datetime, DB-side default `now()`)
- Relationship: `student` (→ AddStudentInfo, backref `attendance`)
- Unique constraint: `(student_id, attendance_date)` — one attendance record per student per day

### MarksTopic (`teacher.py` → table `marks_topic`)
Defines a gradable item within a subject (e.g. "Midterm", "Quiz 1", "Assignment 2"), created by a teacher.
- `marks_topic_id` (PK)
- `marks_topic_name`
- `full_marks` (integer) — max possible score for this topic
- `subject_id` → FK to `subjects.subject_id`
- `teacher_id` → FK to `teacher_info.teacher_id`

### AddMarks (`teacher.py` → table `add_marks`)
A student's score on a specific marks topic.
- `marks_id` (PK, autoincrement)
- `student_id` → FK to `student_data.student_id`
- `subject_id` → FK to `subjects.subject_id`
- `teacher_id` → FK to `teacher_info.teacher_id`
- `marks_topic_id` → FK to `marks_topic.marks_topic_id`
- `obtained_marks` (float)
- `created_at` (datetime, DB-side default `now()`)
- Relationships: `student` (→ AddStudentInfo, backref `marks`), `subject` (→ Subjects, backref `marks`), `topic` (→ MarksTopic, backref `marks`)
- Unique constraint: `(student_id, subject_id, marks_topic_id)` — one score per student per topic per subject

---

## Notable patterns to know before writing new routes/functions

- **No ORM-level relationship on most FKs.** Only `Curriculum`, `TeacherAssignment`, `Attendance`, and `AddMarks` declare `db.relationship(...)`. Everything else (e.g. `AddStudentInfo.department_id`, `TeacherAddInfo.principal_id`) is a bare FK column — you'll need explicit `.query.filter_by(...)` joins rather than dot-access like `student.department`.
- **Session keys currently in use:** `session["teacher"]` (boolean/flag), `session["teacher_id"]`, `session["temp_principal_id"]`, `session["principal_id"]`. Note `temp_principal_id` vs `principal_id` — per the README, this distinction is one of the known fragile spots in the auth flow, so check which one is actually set before relying on it in a new route.
- **Ownership scoping convention:** query `AddStudentInfo` by `teacher_id` (not by `principal_id`) to get "this teacher's students," matching the pattern in `show_student.py`.
- **`group` and `status` are single characters**, not enums — no DB-level constraint on allowed values.
- **Passwords are stored in plain text** (per README, this is a known issue, not yet fixed).
- **`Subjects.student_id`** is an outlier — a nullable FK from Subject to a single Student. Confirm its actual purpose in the relevant route before building a feature that depends on it.