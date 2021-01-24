from flask import (Blueprint,
                   render_template,
                   redirect,
                   request,
                   url_for)

from flask_login import current_user, login_required

from .. import acl
from .. import forms
from vidya import models
import datetime


module = Blueprint('activities',
                   __name__,
                   url_prefix='/activities',
                   )


@module.route('/')
@login_required
def index():
    assignment_schedule = models.assignments.get_assignment_schedule(
            current_user._get_current_object())

    past_assignment_schedule = models.assignments.get_past_assignment_schedule(
            current_user._get_current_object())
    return render_template('/assignments/index.html',
                           assignment_schedule=assignment_schedule,
                           past_assignment_schedule=past_assignment_schedule)


@module.route('/<assignment_id>')
@login_required
def view(assignment_id):
    assignment = models.Assignment.objects.get(id=assignment_id)

    return render_template('/assignments/view.html',
                           assignment=assignment,
                           )


@module.route('/<activity_id>/practice', methods=['GET', 'POST'])
@login_required
def practice(activity_id):
    activity = models.Activity.objects().get(id=activity_id)
    


    now = datetime.datetime.now()
    if activity.started_date > now or now > activity.ended_date:
        message = f'ไม่อยู่ในช่วงเวลาลงเวลา'
        return render_template(
                '/activities/register_fail.html',
                activity=activity,
                message=message,
                )

    form = forms.activities.ActivityRegistrationForm()
    form.section.choices = [(s, s) for s in activity.class_.sections]

    if not form.validate_on_submit():
        return render_template('/activities/practice.html',
                               activity=activity,
                               form=form,
                               )

    if form.student_id.data != current_user.username:
        message = f'รหัสนักศึกษา {form.student_id.data} ไม่ตรงกับบัญชีผู้ใช้'
        return render_template(
                '/activities/register_fail.html',
                activity=activity,
                message=message,
                )

    ap = models.ActivityParticipator()
    ap.user = current_user._get_current_object()
    ap.remark = form.remark.data
    ap.section = form.section.data
    ap.accepted = form.accepted.data
    ap.activity = activity
    if form.location.data:
        ap.location = [float(f) for f in form.location.data.split(',') if len(f.strip()) > 0]
    else:
        ap.location = [0, 0]

    ap.ip_address = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)
    ap.user_agent = request.environ.get('HTTP_USER_AGENT', '')
    ap.client = request.environ.get('HTTP_SEC_CH_UA', '')

    data = form.data
    data.pop('csrf_token')
    ap.data = data
    ap.save()

    return redirect(
            url_for(
                'activities.register_success',
                activity_id=activity.id,
                ))

@module.route('/<activity_id>/practice/success')
@login_required
def register_success(activity_id):
    activity = models.Activity.objects.get(id=activity_id)
    return render_template(
            '/activities/register_success.html',
            activity=activity,
            )


