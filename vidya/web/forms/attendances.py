from wtforms import Form
from wtforms import fields
from wtforms import validators
from wtforms import widgets

import datetime

from .fields import TagListField

from flask_wtf import FlaskForm


class AttendanceTimeForm(FlaskForm):
    started_date = fields.DateTimeField(
        "Started Date",
        format="%Y-%m-%d %H:%M",
        default=datetime.datetime.now,
        validators=[validators.Optional()],
        widget=widgets.TextInput(),
    )

    ended_date = fields.DateTimeField(
        "Ended Data",
        format="%Y-%m-%d %H:%M",
        default=datetime.datetime.now,
        validators=[validators.Optional()],
        widget=widgets.TextInput(),
    )


class AttendanceForm(FlaskForm):
    name = fields.StringField(
        "Name", validators=[validators.InputRequired(), validators.Length(min=3)]
    )
    description = fields.StringField(
        "Description",
        # validators=[validators.InputRequired()],
        widget=widgets.TextArea(),
    )

    sections = fields.SelectMultipleField("Sections")
    required_student_roles = fields.BooleanField("Required student roles")
    required_location = fields.BooleanField("Required location")

    score = fields.IntegerField(
        "Score",
        validators=[validators.InputRequired(), validators.NumberRange(min=0)],
        default=1,
    )
    started_date = fields.DateTimeField(
        "Started Date",
        format="%Y-%m-%d %H:%M",
        validators=[validators.Optional()],
        widget=widgets.TextInput(),
    )

    ended_date = fields.DateTimeField(
        "Ended Data",
        format="%Y-%m-%d %H:%M",
        validators=[validators.Optional()],
        widget=widgets.TextInput(),
    )

    # course = fields.SelectField('Course',)


#            validators=[validators.InputRequired()])
# tags = TagListField('Tags',
#         validators=[validators.InputRequired(),
#                     validators.Length(min=3)])


class AttendanceRegistrationForm(FlaskForm):
    location = fields.HiddenField("current location")
    remark = fields.TextAreaField("ฝากบอก")

    student_roles = fields.SelectMultipleField(
        "บทบาทในชั้นเรียน", validators=[validators.InputRequired()]
    )


class ScheduleAttendanceForm(AttendanceForm):
    repeat = fields.SelectField(
        "Repeat",
        validators=[validators.InputRequired()],
        choices=["Daily", "Weekly", "Monthly"],
    )

    until_date = fields.DateField(
        "Until Data",
        format="%Y-%m-%d",
        default=datetime.date.today,
        validators=[validators.InputRequired()],
        widget=widgets.TextInput(),
    )
