from flask import (Blueprint,
                   render_template,
                   request,
                   redirect,
                   Response,
                   url_for)

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

module = Blueprint('activities',
                   __name__,
                   url_prefix='/activities',
                   )
import json
from bson import ObjectId, DBRef

class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        elif isinstance(o, DBRef):
            return str(o)
        elif isinstance(o, datetime.datetime):
            return o.isoformat()
        elif isinstance(o, models.User):
            return {'id': str(o.id), 
                    'username': o.username,
                    'first_name': o.first_name,
                    'last_name': o.last_name,
                    }
        return json.JSONEncoder.default(self, o)


@module.route('/')
@acl.lecturer_permission.require(http_exception=403)
def index():
    activities = models.Activity.objects(
            owner=current_user._get_current_object())
    return render_template('/administration/activities/index.html',
                           activities=activities)


@module.route('/create', methods=['GET', 'POST'])
@acl.lecturer_permission.require(http_exception=403)
def create():
    class_ = models.Class.objects.get(id=request.args.get('class_id', ''))
    if not class_:
        return 'Class not found'

    form = forms.activities.ActivityForm()
    form.sections.choices = [(s, s) for s in class_.sections]
    if not form.validate_on_submit():
        return render_template('/administration/activities/create-edit.html',
                               form=form)

    data = form.data.copy()
    data.pop('csrf_token')


    activity = models.Activity(**data)
    activity.owner = current_user._get_current_object()
    activity.class_ = class_
    activity.save()

    return redirect(url_for('administration.classes.view',
                            class_id=class_.id))

@module.route('<activity_id>/edit', methods=['GET', 'POST'])
@acl.lecturer_permission.require(http_exception=403)
def edit(activity_id):
    class_ = models.Class.objects.get(id=request.args.get('class_id', ''))
    if not class_:
        return 'Class not found'

    activity = models.Activity.objects.get(id=activity_id)

    
    form = forms.activities.ActivityForm()
    if request.method == 'GET':
        form = forms.activities.ActivityForm(obj=activity)

    form.sections.choices = [(s, s) for s in class_.sections]
    if not form.validate_on_submit():
        return render_template('/administration/activities/create-edit.html',
                               form=form)

    data = form.data.copy()
    data.pop('csrf_token')


    # activity = models.Activity(**data)
    form.populate_obj(activity)
    # activity.owner = current_user._get_current_object()
    # activity.class_ = class_
    activity.save()

    return redirect(url_for('administration.classes.view',
                            class_id=class_.id))

@module.route('/schedule', methods=['GET', 'POST'])
@acl.lecturer_permission.require(http_exception=403)
def schedule():
    class_ = models.Class.objects.get(id=request.args.get('class_id', ''))
    if not class_:
        return 'Class not found'

    form = forms.activities.ScheduleActivityForm()
    form.sections.choices = [(s, s) for s in class_.sections]
    if request.method == 'GET':
        if len(class_.sections) == 1:
            form.sections.data = class_.sections[0]

    if not form.validate_on_submit():
        return render_template(
                '/administration/activities/schedule.html',
                form=form)

    data = form.data.copy()
    data.pop('csrf_token')

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
        activity = models.Activity()
        form.populate_obj(activity)
        activity.name = f'{form.name.data} {started_date} - {ended_date}'
        activity.owner = current_user._get_current_object()
        activity.class_ = class_
        activity.started_date = started_date
        activity.ended_date = ended_date
        
        activity.save()

    return redirect(url_for('administration.classes.view',
                            class_id=class_.id))


@module.route('/<activity_id>/delete')
@acl.lecturer_permission.require(http_exception=403)
def delete(activity_id):
    activity = models.Activity.objects.get(id=activity_id)
    class_ = activity.class_
    activity.delete()

    return redirect(url_for('administration.classes.view',
                            class_id=class_.id))


@module.route('/<activity_id>')
@acl.lecturer_permission.require(http_exception=403)
def view(activity_id):
    activity = models.Activity.objects.get(id=activity_id)
    challenges = models.Challenge.objects()

    choices = [(str(q.id), q.name) for q in challenges \
            if q not in activity.challenges]

    form = forms.activities.ChallengeAddingForm()
    form.challenges.choices = choices

    return render_template('/administration/activities/view.html',
                           activity=activity,
                           form=form)

@module.route('/<activity_id>/participators')
@acl.lecturer_permission.require(http_exception=403)
def list_participators(activity_id):
    activity = models.Activity.objects.get(id=activity_id)
    participators = models.ActivityParticipator.objects(activity=activity)

    # participators = sorted(participators, key=lambda p: p.section)


    return render_template('/administration/activities/list-participators.html',
                           activity=activity,
                           participators=participators,
                           )


@module.route('/<activity_id>/map/<section>')
@login_required
@acl.lecturer_permission.require(http_exception=403)
def show_map(activity_id, section):
    activity = models.Activity.objects.get(id=activity_id)

    participators = []
    if section == 'all':
        participators = models.ActivityParticipator.objects(activity=activity)
    else:
        if section in activity.class_.limited_enrollment:
            users = []
            for sid in activity.class_.limited_enrollment[section]:
                user = models.User.objects(username=sid).first()
                if user:
                    users.append(user)
        
            participators = models.ActivityParticipator.objects(
                    activity=activity,
                    user__in=users,
                    )


    odata = []
    for p in participators:
        pdata = p.to_mongo().to_dict()
        pdata['user'] = p.user
        pdata['section'] = activity.class_.get_section(p.user)
        odata.append(pdata)
    
    data = JSONEncoder().encode(odata)

    data = data.replace('\\"', '\\\\"')
    data = data.replace("\\r\\n", '\\\\r\\\\n')
    print(participators)
    return render_template('/administration/activities/show-map.html',
                           activity=activity,
                           participators=participators,
                           data=data,
                           )


@module.route('/<activity_id>/export-participators')
@acl.lecturer_permission.require(http_exception=403)
def export_participators(activity_id):
    activity = models.Activity.objects.get(id=activity_id)
    class_ = activity.class_
    section = request.args.get('section')
    participators = []

    if section == 'all':
        participators = models.ActivityParticipator.objects(activity=activity)
    else:
        participators = models.ActivityParticipator.objects(activity=activity, section=section)


    # participators = sorted(participators, key=lambda p: p.section)

    header = ['Student ID',
              'First Name',
              'Last Name',
              'Section',
              'Role',
              'Registration Time',
              'Location',
              'IP Address',
              'Client',
              'User Agent']

    row_list = []
    for participator in participators:

        data = {
            'Student ID': participator.user.username,
            'First Name': participator.user.first_name,
            'Last Name': participator.user.last_name,
            'Section': class_.get_section(participator.user),
            'Role': ', '.join(participator.student_roles),
            'Registration Time': participator.registration_date,
            'Location': ','.join(
                [str(l) for l in participator.location]) if participator.location else '',
            'IP Address': participator.ip_address,
            'Client': participator.client,
            'User Agent': participator.user_agent,
            }

        row_list.append(data)

    df = pandas.DataFrame(row_list)
    df.index += 1
    output = io.BytesIO()
    writer = pandas.ExcelWriter(output, engine='xlsxwriter')
    df.to_excel(writer, sheet_name='Sheet1')
    writer.save()

    return Response(
            output.getvalue(),
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            headers={
                'Content-disposition': f'attachment; filename*=UTF-8\'\'{quote(activity.name.encode("utf-8"))}.xlsx'})



