from wtforms import Form
from wtforms import fields
from wtforms import validators
from wtforms import widgets

from .fields import TagListField, TextListField

from flask_wtf import FlaskForm


class TeachingAssistantAddingForm(FlaskForm):
    users = fields.SelectMultipleField('Users')


class LimitedEnrollmentForm(Form):
    method = fields.SelectField('Method',
            validators=[validators.InputRequired()]
            )
    grantees = TextListField('Grantees',
            validators=[validators.InputRequired(),
                        validators.Length(min=1)])
    # grantees = fields.StringField('Grantees',
    #         widget=widgets.TextArea())

class StudentRegisterForm(FlaskForm):
    section = fields.SelectField('section',
            validators=[validators.InputRequired()]
            )
    student_ids = TextListField(
            'Student ID',
            validators=[
                validators.InputRequired(),
                validators.Length(min=1)],
            )


class ClassForm(FlaskForm):
    name = fields.StringField(
            'Name',
            validators=[validators.InputRequired(),
                        validators.Length(min=3)])
    description = fields.StringField('Description',
            validators=[validators.InputRequired()],
            widget=widgets.TextArea())
    code = fields.StringField('Code')
    # course = fields.SelectField('Course',
    #         validators=[validators.InputRequired()])

    # limited = fields.BooleanField('Limited Class', default=True)
    # limited_enrollment = fields.FormField(LimitedEnrollmentForm)

    started_date = fields.DateField(
            'Started Date',
            format='%Y-%m-%d',
            widget=widgets.TextInput(),
            )
    ended_date = fields.DateField(
            'Ended Data',
            format='%Y-%m-%d',
            widget=widgets.TextInput(),
            )

    contributors = fields.SelectMultipleField('Contributors')
    sections = TagListField(
            'Sections',
            validators=[validators.InputRequired(),
                        validators.Length(min=1)])

    student_roles = TagListField(
            'Student Roles')
    tags = TagListField(
            'Tags',
            validators=[validators.InputRequired(),
                        validators.Length(min=3)])


