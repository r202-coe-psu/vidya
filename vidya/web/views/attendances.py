from flask import Blueprint, render_template, redirect, request, url_for

from flask_login import current_user, login_required

from .. import acl
from .. import forms
from vidya import models
import datetime


module = Blueprint(
    "attendances",
    __name__,
    url_prefix="/attendances",
)


@module.route("/")
@login_required
def index():
    assignment_schedule = models.assignments.get_assignment_schedule(
        current_user._get_current_object()
    )

    past_assignment_schedule = models.assignments.get_past_assignment_schedule(
        current_user._get_current_object()
    )
    return render_template(
        "/assignments/index.html",
        assignment_schedule=assignment_schedule,
        past_assignment_schedule=past_assignment_schedule,
    )


@module.route("/<assignment_id>")
@login_required
def view(assignment_id):
    assignment = models.Assignment.objects.get(id=assignment_id)

    return render_template(
        "/assignments/view.html",
        assignment=assignment,
    )


@module.route("/<attendance_id>/checkin", methods=["GET", "POST"])
@login_required
def checkin(attendance_id):
    attendance = models.Attendance.objects().get(id=attendance_id)
    class_ = attendance.class_

    participator = models.Attendee.objects(
        user=current_user._get_current_object(), attendance=attendance
    ).first()

    if participator:
        return redirect(
            url_for(
                "attendances.checkin_success",
                attendance_id=attendance.id,
            )
        )

    check_section = False
    for k, v in class_.limited_enrollment.items():
        if current_user.username in v:
            check_section = True

    now = datetime.datetime.now()
    if not check_section:
        message = f"ไม่พบรหัสนักศึกษาระบุไว้ในเรียน"
        return render_template(
            "/attendances/checkin_fail.html",
            attendance=attendance,
            message=message,
            current_date=now,
        )

    if attendance.started_date > now or now > attendance.ended_date:
        message = f"ไม่อยู่ในช่วงเวลาลงเวลา"
        return render_template(
            "/attendances/checkin_fail.html",
            attendance=attendance,
            message=message,
            current_date=now,
        )

    form = forms.attendances.AttendanceRegistrationForm()

    if not attendance.required_location:
        del form.location

    if not attendance.required_student_roles:
        del form.student_roles
    else:
        form.student_roles.choices = [(r, r) for r in class_.student_roles]

    if not form.validate_on_submit():
        return render_template(
            "/attendances/checkin.html",
            attendance=attendance,
            form=form,
        )

    ap = models.Attendee()
    ap.user = current_user._get_current_object()
    ap.remark = form.remark.data
    ap.attendance = attendance

    if attendance.required_location:
        if form.location.data:
            ap.location = [
                float(f) for f in form.location.data.split(",") if len(f.strip()) > 0
            ]
        else:
            ap.location = [0, 0]

    if attendance.required_student_roles:
        ap.student_roles = form.student_roles.data

    ap.ip_address = request.environ.get("HTTP_X_REAL_IP", request.remote_addr)
    ap.user_agent = request.environ.get("HTTP_USER_AGENT", "")
    ap.client = request.environ.get("HTTP_SEC_CH_UA", "")

    data = form.data
    data.pop("csrf_token")
    ap.data = data
    ap.save()

    return redirect(
        url_for(
            "attendances.checkin_success",
            attendance_id=attendance.id,
        )
    )


@module.route("/<attendance_id>/practice/success")
@login_required
def checkin_success(attendance_id):
    attendance = models.Attendance.objects.get(id=attendance_id)
    return render_template(
        "/attendances/checkin_success.html",
        attendance=attendance,
    )
