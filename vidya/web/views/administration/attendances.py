from flask import Blueprint, render_template, request, redirect, Response, url_for

from flask_login import current_user, login_required

from vidya.web import acl, forms
from vidya import models

import pandas
import io
from urllib.parse import quote
from dateutil import rrule
import json
import bson
import datetime


import json
from bson import ObjectId, DBRef

module = Blueprint(
    "attendances",
    __name__,
    url_prefix="/attendances",
)


class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        elif isinstance(o, DBRef):
            return str(o)
        elif isinstance(o, datetime.datetime):
            return o.isoformat()
        elif isinstance(o, models.User):
            return {
                "id": str(o.id),
                "username": o.username,
                "first_name": o.first_name,
                "last_name": o.last_name,
            }
        return json.JSONEncoder.default(self, o)


@module.route("/")
@acl.roles_required("lecturer")
def index():
    attendances = models.Attendance.objects(owner=current_user._get_current_object())
    return render_template(
        "/administration/attendances/index.html", attendances=attendances
    )


@module.route("/create", methods=["GET", "POST"])
@acl.roles_required("lecturer")
def create():
    class_ = models.Class.objects.get(id=request.args.get("class_id", ""))
    if not class_:
        return "Class not found"

    form = forms.attendances.AttendanceForm()
    form.sections.choices = [(s, s) for s in class_.sections]
    if not form.validate_on_submit():
        return render_template(
            "/administration/attendances/create-edit.html", form=form
        )

    data = form.data.copy()
    data.pop("csrf_token")

    attendance = models.Attendance(**data)
    attendance.owner = current_user._get_current_object()
    attendance.class_ = class_
    attendance.save()

    return redirect(url_for("administration.classes.view", class_id=class_.id))


@module.route("<attendance_id>/edit", methods=["GET", "POST"])
@acl.roles_required("lecturer")
def edit(attendance_id):
    class_ = models.Class.objects.get(id=request.args.get("class_id", ""))
    if not class_:
        return "Class not found"

    attendance = models.Attendance.objects.get(id=attendance_id)

    form = forms.attendances.AttendanceForm()
    if request.method == "GET":
        form = forms.attendances.AttendanceForm(obj=attendance)

    form.sections.choices = [(s, s) for s in class_.sections]
    if not form.validate_on_submit():
        return render_template(
            "/administration/attendances/create-edit.html", form=form
        )

    data = form.data.copy()
    data.pop("csrf_token")

    # attendance = models.Attendance(**data)
    form.populate_obj(attendance)
    # attendance.owner = current_user._get_current_object()
    # attendance.class_ = class_
    attendance.save()

    return redirect(url_for("administration.classes.view", class_id=class_.id))


@module.route("/schedule", methods=["GET", "POST"])
@acl.roles_required("lecturer")
def schedule():
    class_ = models.Class.objects.get(id=request.args.get("class_id", ""))
    if not class_:
        return "Class not found"

    form = forms.attendances.ScheduleAttendanceForm()
    form.sections.choices = [(s, s) for s in class_.sections]
    if request.method == "GET":
        if len(class_.sections) == 1:
            form.sections.data = class_.sections[0]

    if not form.validate_on_submit():
        return render_template("/administration/attendances/schedule.html", form=form)

    data = form.data.copy()
    data.pop("csrf_token")

    freq_data = dict(
        Daily=rrule.DAILY,
        Weekly=rrule.WEEKLY,
        Monthly=rrule.MONTHLY,
    )

    diff = form.ended_date.data - form.started_date.data
    rrule_iter = rrule.rrule(
        freq=freq_data[form.repeat.data],
        dtstart=form.started_date.data,
        until=form.until_date.data,
    )
    # print(list(rrule_iter))
    for d in rrule_iter:
        started_date = d
        ended_date = d + diff
        attendance = models.Attendance()
        form.populate_obj(attendance)
        attendance.name = f"{form.name.data} {started_date} - {ended_date}"
        attendance.owner = current_user._get_current_object()
        attendance.class_ = class_
        attendance.started_date = started_date
        attendance.ended_date = ended_date

        attendance.save()

    return redirect(url_for("administration.classes.view", class_id=class_.id))


@module.route("/<attendance_id>/delete")
@acl.roles_required("lecturer")
def delete(attendance_id):
    attendance = models.Attendance.objects.get(id=attendance_id)
    class_ = attendance.class_
    attendance.delete()

    return redirect(url_for("administration.classes.view", class_id=class_.id))


@module.route("/<attendance_id>")
@acl.roles_required("lecturer")
def view(attendance_id):
    attendance = models.Attendance.objects.get(id=attendance_id)
    challenges = models.Challenge.objects()

    choices = [
        (str(q.id), q.name) for q in challenges if q not in attendance.challenges
    ]

    form = forms.attendances.ChallengeAddingForm()
    form.challenges.choices = choices

    return render_template(
        "/administration/attendances/view.html", attendance=attendance, form=form
    )


@module.route("/<attendance_id>/attendees")
@acl.roles_required("lecturer")
def list_attendees(attendance_id):
    attendance = models.Attendance.objects.get(id=attendance_id)
    attendees = models.Attendee.objects(attendance=attendance)

    # attendees = sorted(attendees, key=lambda p: p.section)

    return render_template(
        "/administration/attendances/list-attendees.html",
        attendance=attendance,
        attendees=attendees,
    )


@module.route("/<attendance_id>/map/<section>")
@login_required
@acl.roles_required("lecturer")
def show_map(attendance_id, section):
    attendance = models.Attendance.objects.get(id=attendance_id)

    attendees = []
    if section == "all":
        attendees = models.Attendee.objects(attendance=attendance)
    else:
        if section in attendance.class_.limited_enrollment:
            users = []
            for sid in attendance.class_.limited_enrollment[section]:
                user = models.User.objects(username=sid).first()
                if user:
                    users.append(user)

            attendees = models.Attendee.objects(
                attendance=attendance,
                user__in=users,
            )

    odata = []
    for p in attendees:
        pdata = p.to_mongo().to_dict()
        pdata["user"] = p.user
        pdata["section"] = attendance.class_.get_section(p.user)
        odata.append(pdata)

    data = JSONEncoder().encode(odata)
    data = data.replace('\\"', '\\\\"')
    data = data.replace("\\r\\n", "\\\\r\\\\n")
    return render_template(
        "/administration/attendances/show-map.html",
        attendance=attendance,
        attendees=attendees,
        data=data,
    )


@module.route("/<attendance_id>/export-attendees")
@acl.roles_required("lecturer")
def export_attendees(attendance_id):
    attendance = models.Attendance.objects.get(id=attendance_id)
    class_ = attendance.class_
    section = request.args.get("section")
    attendees = []

    if section == "all":
        attendees = models.Attendee.objects(attendance=attendance)
    else:
        attendees = models.Attendee.objects(attendance=attendance, section=section)

    # attendees = sorted(attendees, key=lambda p: p.section)

    header = [
        "Student ID",
        "First Name",
        "Last Name",
        "Section",
        "Role",
        "Registration Time",
        "Location",
        "IP Address",
        "Client",
        "User Agent",
    ]

    row_list = []
    for attendee in attendees:
        data = {
            "Student ID": attendee.user.username,
            "First Name": attendee.user.first_name,
            "Last Name": attendee.user.last_name,
            "Section": class_.get_section(attendee.user),
            "Role": ", ".join(attendee.student_roles),
            "Registration Time": attendee.registration_date,
            "Location": ",".join([str(l) for l in attendee.location])
            if attendee.location
            else "",
            "IP Address": attendee.ip_address,
            "Client": attendee.client,
            "User Agent": attendee.user_agent,
        }

        row_list.append(data)

    df = pandas.DataFrame(row_list)
    df.index += 1
    output = io.BytesIO()
    writer = pandas.ExcelWriter(output, engine="xlsxwriter")
    df.to_excel(writer, sheet_name="Sheet1")

    return Response(
        output.getvalue(),
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-disposition": f'attachment; filename*=UTF-8\'\'{quote(attendance.name.encode("utf-8"))}.xlsx'
        },
    )
