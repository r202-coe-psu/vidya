import datetime

from wtforms import Form
from wtforms import fields
from wtforms import validators
from wtforms import widgets

from flask_mongoengine.wtf import model_form
from flask_wtf import FlaskForm

from vidya import models

from .fields import TagListField


BaseAttendeeForm = model_form(
    models.Attendee,
    FlaskForm,
    only=["student_roles"],
    field_args=dict(student_roles=dict(label="Roles")),
)


class AttendeeRoleForm(BaseAttendeeForm):
    student_roles = fields.SelectMultipleField(
        "บทบาทในชั้นเรียน", validators=[validators.InputRequired()]
    )
