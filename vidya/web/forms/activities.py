from wtforms import Form
from wtforms import fields
from wtforms import validators
from wtforms import widgets

import datetime

from .fields import TagListField

from flask_wtf import FlaskForm

class ActivityTimeForm(FlaskForm):
    started_date = fields.DateTimeField('Started Date',
            format='%Y-%m-%d %H:%M',
            default=datetime.datetime.now(),
            validators=[validators.Optional()],
            widget=widgets.TextInput(),
            )

    ended_date = fields.DateTimeField('Ended Data',
            format='%Y-%m-%d %H:%M',
            default=datetime.datetime.now(),
            validators=[validators.Optional()],
            widget=widgets.TextInput(),
            )



class ActivityForm(FlaskForm):
    name = fields.StringField('Name',
            validators=[validators.InputRequired(),
                        validators.Length(min=3)])
    description = fields.StringField('Description',
            # validators=[validators.InputRequired()],
            widget=widgets.TextArea())
    score = fields.IntegerField('Score',
            validators=[validators.InputRequired(),
                validators.NumberRange(min=0)],
            default=0)
    started_date = fields.DateTimeField('Started Date',
            format='%Y-%m-%d %H:%M',
            validators=[validators.Optional()],
            widget=widgets.TextInput(),
            )

    ended_date = fields.DateTimeField('Ended Data',
            format='%Y-%m-%d %H:%M',
            validators=[validators.Optional()],
            widget=widgets.TextInput(),
            )


    # course = fields.SelectField('Course',)
#            validators=[validators.InputRequired()])
    # tags = TagListField('Tags',
    #         validators=[validators.InputRequired(),
    #                     validators.Length(min=3)])


class ActivityRegistrationForm(FlaskForm):
    first_name = fields.StringField('ชื่อ',
            validators=[validators.InputRequired(),
                        validators.Length(min=1)])

    last_name = fields.StringField('นามสกุล',
            validators=[validators.InputRequired(),
                        validators.Length(min=1)])
    student_id = fields.StringField('รหัสนักศึกษา',
            validators=[validators.InputRequired(),
                        validators.Length(min=3, max=20)])
   
    section = fields.SelectField('ตอน')
    location = fields.HiddenField('current location')
    remark = fields.TextAreaField('หากไม่สามารถใช้งาน GPS ได้กรุณาให้เหตุผล')

    accepted = fields.BooleanField(
            'เข้าใจและยอมรับข้อตกลงในการสอบ',
            default=False,
            validators=[validators.InputRequired()]
            )

