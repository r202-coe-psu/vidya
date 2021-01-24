from flask import Blueprint, render_template
from flask_login import login_required, current_user

from vidya import models
import mongoengine as me

import datetime

module = Blueprint('dashboard', __name__, url_prefix='/dashboard')
subviews = []


def index_admin():
    
    now = datetime.datetime.now()
    classes = models.Class.objects(
            me.Q(owner=current_user._get_current_object()) | 
            me.Q(contributors=current_user._get_current_object()))
    return render_template('/dashboard/index-admin.html',
                           now=datetime.datetime.now(),
                           available_classes=classes)


def index_user():

    user = current_user
    now = datetime.datetime.now()

    available_classes = models.Class.objects(
            (me.Q(started_date__lte=now) &
                me.Q(ended_date__gte=now))
            ).order_by('ended_date')

    activities = models.Activity.objects(class___in=available_classes)
    return render_template('/dashboard/index.html',
                           available_classes=available_classes,
                           activities=activities,
                           now=datetime.datetime.now(),
                           )


    # ass_schedule = []
    # for class_ in available_classes:
    #     if not class_.is_enrolled(user.id):
    #         continue

    #     for ass_t in class_.assignment_schedule:
    #         if ass_t.started_date <= now and now < ass_t.ended_date:
    #             ass_schedule.append(
    #                     dict(assignment_schedule=ass_t,
    #                          class_=class_))

    # def order_by_ended_date(e):
    #     return e['assignment_schedule'].ended_date

    # ass_schedule.sort(key=order_by_ended_date)

    # return render_template('/dashboard/index.html',
    #                        available_classes=available_classes,
    #                        assignment_schedule=ass_schedule,
    #                        now=datetime.datetime.now(),
    #                        )


@module.route('/')
@login_required
def index():
    user = current_user._get_current_object()
    if 'lecturer' in user.roles or 'admin' in user.roles:
        return index_admin()
    
    return index_user()
