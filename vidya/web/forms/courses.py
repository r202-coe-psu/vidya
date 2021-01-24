from wtforms import Form
from wtforms import fields
from wtforms import validators
from wtforms import widgets

from flask_wtf import FlaskForm

from .fields import TagListField


class CourseForm(FlaskForm):
    name = fields.StringField('Name',
            validators=[validators.InputRequired(),
                        validators.Length(min=3)])
    description = fields.StringField('Description',
            validators=[validators.InputRequired()],
            widget=widgets.TextArea())
    tags = TagListField('Tags',
            validators=[validators.InputRequired(),
                        validators.Length(min=3)])
