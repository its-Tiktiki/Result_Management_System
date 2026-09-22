'''There is AddStudentForm and SelectSemesterAndDepartmentForm'''

from flask_wtf import FlaskForm
from wtforms import SelectField,IntegerField,StringField,SubmitField,DateTimeField
from wtforms.validators import DataRequired
from wtforms import SelectField

class AddStudentForm(FlaskForm):
    student_roll = IntegerField("Student Roll",validators=[DataRequired()])
    student_full_name = StringField("Student Name",validators=[DataRequired()])
    department_id = SelectField("Department",coerce=int, choices=[])
    sessions = StringField("Session",validators=[DataRequired()])
    semester = SelectField("Semester",coerce=int,choices=[])
    group = SelectField("If exit. Select group",choices=[("None"),("A"),("B")])
    submit = SubmitField("Add Student")



class SelectSemesterAndDepartmentForm(FlaskForm):
    department_id = SelectField("Select Department",choices=[],coerce=int)
    semester = SelectField("Select Semester",choices=[],coerce=int)
    sessions = SelectField("Select Session",choices=[],validators=[DataRequired()])
    group = SelectField("Select Group",choices=[])
    submit = SubmitField("Load Student")