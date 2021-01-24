from wtforms import Form
from wtforms import fields
from wtforms import validators

from flask_wtf import FlaskForm
from flask import request

from .. import models

class Profile(FlaskForm):
    first_name = fields.StringField(
            'First Name',
            validators=[validators.InputRequired()])
    last_name = fields.StringField(
            'Last Name',
            validators=[validators.InputRequired()])

    student_id = fields.StringField('Student ID')
    thai_first_name = fields.StringField('Thai First Name')
    thai_last_name = fields.StringField('Thai Last Name')
    organization = fields.StringField('Organization')
