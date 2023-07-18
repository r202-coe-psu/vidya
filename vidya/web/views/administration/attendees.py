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
    "attendees",
    __name__,
    url_prefix="/attendees",
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


@module.route("/<attendee_id>/edit", methods=["GET", "POST"])
@acl.roles_required("lecturer")
def edit_roles(attendee_id):
    attendee = models.Attendee.objects.get(id=attendee_id)
    form = forms.attendees.AttendeeRoleForm(obj=attendee)
    form.student_roles.choices = attendee.attendance.class_.student_roles

    if not form.validate_on_submit():
        return render_template(
            "/administration/attendees/roles.html", form=form, attendee=attendee
        )

    form.populate_obj(attendee)
    attendee.updated_date = datetime.datetime.now()
    attendee.save()

    return redirect(
        url_for(
            "administration.attendances.list_attendees",
            attendance_id=attendee.attendance.id,
        )
    )
