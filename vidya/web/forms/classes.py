from wtforms import Form
from wtforms import fields
from wtforms import validators
from wtforms import widgets

from .fields import TagListField, TextListField

from flask_wtf import FlaskForm


class TeachingAssistantAddingForm(FlaskForm):
    users = fields.SelectMultipleField("Users")


class LimitedEnrollmentForm(Form):
    section = fields.StringField("Section", validators=[validators.InputRequired()])
    student_ids = TextListField(
        "Student ID",
        # validators=[
        #     validators.InputRequired(),
        #     validators.Length(min=1)],
    )


class StudentRegisterForm(FlaskForm):
    limited_enrollments = fields.FieldList(fields.FormField(LimitedEnrollmentForm))
    # limited_enrollments = fields.FormField(LimitedEnrollmentForm)


class ClassForm(FlaskForm):
    name = fields.StringField(
        "Name", validators=[validators.InputRequired(), validators.Length(min=3)]
    )
    description = fields.StringField(
        "Description",
        validators=[validators.InputRequired()],
        widget=widgets.TextArea(),
    )
    code = fields.StringField("Code")
    score_items = fields.StringField(
        "Score Item",
        widget=widgets.TextArea(),
        default={},
        validators=[validators.Optional()],
    )

    started_date = fields.DateField(
        "Started Date",
        format="%Y-%m-%d",
        widget=widgets.TextInput(),
    )
    ended_date = fields.DateField(
        "Ended Data",
        format="%Y-%m-%d",
        widget=widgets.TextInput(),
    )

    contributors = fields.SelectMultipleField("Contributors")
    sections = TagListField(
        "Sections", validators=[validators.InputRequired(), validators.Length(min=1)]
    )

    student_roles = TagListField("Student Roles")
    tags = TagListField(
        "Tags", validators=[validators.InputRequired(), validators.Length(min=3)]
    )
