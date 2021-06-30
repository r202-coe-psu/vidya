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


@module.route('/<activity_id>/register', methods=['GET', 'POST'])
@login_required
def register(activity_id):
    activity = models.Activity.objects().get(id=activity_id)
    class_ = activity.class_

    participator = models.ActivityParticipator.objects(
            user=current_user._get_current_object(),
            activity=activity).first()
    
    if participator:
        return redirect(
            url_for(
                'activities.register_success',
                activity_id=activity.id,
                ))

    check_section = False
    for k, v in class_.limited_enrollment.items():
        if current_user.username in v:
            check_section = True

    if not check_section:
        message = f'ไม่พบรหัสนักศึกษาระบุไ้วในชั้นเรียน'
        return render_template(
                '/activities/register_fail.html',
                activity=activity,
                message=message,
                )

    now = datetime.datetime.now()
    if activity.started_date > now or now > activity.ended_date:
        message = f'ไม่อยู่ในช่วงเวลาลงเวลา'
        return render_template(
                '/activities/register_fail.html',
                activity=activity,
                message=message,
                )

    form = forms.activities.ActivityRegistrationForm()

    if not activity.required_location:
        del form.location

    if not activity.required_student_roles:
        del form.student_roles
    else:
        form.student_roles.choices = [(r, r) for r in class_.student_roles]

    if not form.validate_on_submit():
        return render_template('/activities/register.html',
                               activity=activity,
                               form=form,
                               )


    ap = models.ActivityParticipator()
    ap.user = current_user._get_current_object()
    ap.remark = form.remark.data
    ap.activity = activity

    ap.location = [0, 0]
    if activity.required_location:
        if form.location.data:
            ap.location = [float(f) for f in form.location.data.split(',') if len(f.strip()) > 0]

    if activity.required_student_roles:
        ap.student_roles = form.student_roles.data

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


