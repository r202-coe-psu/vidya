from flask import (Blueprint,
                   render_template,
                   url_for,
                   redirect,
                   request,
                   Response,
                   send_file
                   )
from flask_login import current_user, login_required

from vidya.web import acl, forms
from vidya import models

import mongoengine as me

import datetime
import csv
import pandas
import io
import qrcode
import base64
from urllib.parse import quote

module = Blueprint('classes',
                   __name__,
                   url_prefix='/classes',
                   )


@module.route('/')
@acl.lecturer_permission.require(http_exception=403)
def index():
    classes = models.Class.objects(
                me.Q(owner=current_user._get_current_object()) |
                me.Q(contributors=current_user._get_current_object())
            ).order_by('-id')
    return render_template('/administration/classes/index.html',
                           classes=classes)


@module.route('/<class_id>/edit', methods=['GET', 'POST'])
# @acl.allows.requires(acl.is_class_owner)
def edit(class_id):
    # courses = models.Course.objects()

    class_ = models.Class.objects.get(id=class_id)
    form = forms.classes.ClassForm(obj=class_)
    # le_form = forms.classes.LimitedEnrollmentForm(
    #         obj=class_.limited_enrollment)

    # form.limited_enrollment = le_form
    # course_choices = [(str(c.id), c.name) for c in courses]
    # form.course.choices = course_choices
    # if request.method == 'GET':
        # form.course.data = str(class_.course.id)
    # method_choices = [('email', 'Email'), ('student_id', 'Student ID')]
    # form.limited_enrollment.method.choices = method_choices

    lecturers = models.User.objects(roles='lecturer')
    form.contributors.choices = [(str(u.id), f'{u.first_name} {u.last_name}') for u in lecturers]
    if request.method == 'GET':
        form.contributors.data = [
                str(u.id) for u in class_.contributors]


    if not form.validate_on_submit():
        return render_template('/administration/classes/create-edit.html',
                               form=form)

    form.populate_obj(class_)
    # course = models.Course.objects.get(id=form.course.data)
    # class_.course = course
    class_.contributors = [models.User.objects.get(id=uid) for uid in form.contributors.data]
    class_.save()
    return redirect(url_for('administration.classes.view', class_id=class_.id))


@module.route('/<class_id>/delete')
# @acl.allows.requires(acl.is_class_owner)
def delete(class_id):

    class_ = models.Class.objects.get(id=class_id)
    class_.delete()
    return redirect(url_for('administration.classes.index'))


@module.route('/create', methods=['GET', 'POST'])
@acl.lecturer_permission.require(http_exception=403)
def create():
    form = forms.classes.ClassForm()
    # courses = models.Course.objects()

    # course_choices = [(str(c.id), c.name) for c in courses]
    # form.course.choices = course_choices
    # method_choices = [('email', 'Email'), ('student_id', 'Student ID')]
    # form.limited_enrollment.method.choices = method_choices
    lecturers = models.User.objects(roles='lecturer')
    form.contributors.choices = [(str(u.id), f'{u.first_name} {u.last_name}') for u in lecturers]
    form.contributors.choices.insert(0, ('', ''))

    if not form.validate_on_submit():
        print(form.errors)
        return render_template('/administration/classes/create-edit.html',
                               form=form)
    data = form.data.copy()
    data.pop('csrf_token')
    data.pop('contributors')
    # data.pop('limited_enrollment')

    class_ = models.Class(**data)
    class_.owner = current_user._get_current_object()
    for uid in form.contributors.data:
        u = models.User.objects(id=uid).first()
        if u:
            class_.contributors.append(u)
    class_.save()
    return redirect(url_for('administration.classes.index'))


@module.route('/<class_id>/add-student', methods=['GET', 'POST'])
@acl.lecturer_permission.require(http_exception=403)
def add_students(class_id):
    class_ = models.Class.objects.get(id=class_id)
    form = forms.classes.StudentRegisterForm(
            obj=dict(limited_enrollment=[
                    dict(section=s, student_ids=sids)
                         for s, sids in class_.limited_enrollment.items()]
                         )
            )
    if not form.validate_on_submit():
        return render_template(
                '/administration/classes/add-update-students.html',
                form=form,
                class_=class_,
                )

    section = form.section.data
    class_.limited_enrollment[section] = form.student_ids.data

    class_.limited_enrollment[section].sort()
    class_.save()
    
    return redirect(
            url_for('administration.classes.list_students', class_id=class_.id)
            )

@module.route('/<class_id>')
@login_required
# @acl.allows.requires(acl.is_class_owner_and_contributors)
def view(class_id):
    class_ = models.Class.objects.get(id=class_id)
    activities = models.Activity.objects(class_=class_).order_by('started_date')

    qr_images = dict()
    for activity in activities:
        url = request.url_root.replace(request.script_root, '')[:-1] + url_for('activities.register', activity_id=activity.id)

        qr = qrcode.QRCode(
            version=7,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=2,
        )
        qr.add_data(url)
        qr.make(fit=True)

        img = qr.make_image().convert('RGB')

        img_io = io.BytesIO()
        img.save(img_io, 'JPEG', quality=100)
        encoded = base64.b64encode(img_io.getvalue()).decode("ascii")

        qr_images[activity.id] = dict(
                image=encoded,
                url=url
            )
        
    now = datetime.datetime.now()
    return render_template('/administration/classes/view.html',
                           class_=class_,
                           activities=activities,
                           qr_images=qr_images,
                           now=now,
                           )


@module.route('/<class_id>/set-activity-time/<activity_id>',
              methods=['GET', 'POST'])
# @acl.allows.requires(acl.is_class_owner_and_contributors)
def set_activity_time(class_id, activity_id):
    class_ = models.Class.objects.get(id=class_id)
    activity = models.Activity.objects.get(id=activity_id)


    form = forms.activities.ActivityTimeForm()
    if request.method == 'GET':
        data = dict(
                started_date=activity.started_date,
                ended_date=activity.ended_date,
                )

        form = forms.activities.ActivityTimeForm(data=data)


    if not form.validate_on_submit():
        return render_template(
            '/administration/classes/set-activity-time.html',
            form=form,
            activity=activity)

    activity.started_date = form.started_date.data
    activity.ended_date = form.ended_date.data

    activity.save()

    return redirect(url_for('administration.classes.view', class_id=class_id))


@module.route('/<class_id>/users')
# @acl.allows.requires(acl.is_class_owner)
def list_students(class_id):
    class_ = models.Class.objects.get(id=class_id)

    # enrollments = class_.get_enrollments()
    # enrollments = sorted(enrollments,
    #                      key=lambda e: e.user.first_name)

    # unenrollments = []
    # never_login = []
    # le = class_.limited_enrollment
    # for grantee in le.grantees:
    #     if le.method == 'email':
    #         user = models.User.objects(email=grantee).first()
    #     elif le.method == 'student_id':
    #         user = models.User.objects(username=grantee).first()

    #     if user is None:
    #         never_login.append(grantee)
    #         continue

    #     if not class_.is_enrolled(user=user):
    #         unenrollments.append(user)
    users = {}
    section = request.args.get('section', 'all')
    sids = []
    if section == 'all':
        for k, v in class_.limited_enrollment.items():
            for sid in v:
                sids.append((sid, k))
    else:
        for sid in class_.limited_enrollment[section]:
            sids.append((sid, section))

    for sid, _ in sids:
        user = models.User.objects(username=sid).first()
        users[sid] = user


    return render_template('/administration/classes/list-users.html',
                           class_=class_,
                           users=users,
                           sids=sids,
                           section=section,
                           # enrollments=enrollments,
                           # unenrollments=unenrollments,
                           # never_login=never_login,
                           )


@module.route('/<class_id>/users/<user_id>')
# @acl.allows.requires(acl.is_class_owner)
def show_user_score(class_id, user_id):
    class_ = models.Class.objects.get(id=class_id)
    user = models.User.objects.get(id=user_id)
    assignments = class_.course.assignments

    return render_template('/administration/classes/show-user-score.html',
                           class_=class_,
                           user=user,
                           assignments=assignments)


@module.route('/<class_id>/users/<user_id>/assignments/<assignment_id>')
# @acl.allows.requires(acl.is_class_owner)
def show_user_assignment(class_id, user_id, assignment_id):
    class_ = models.Class.objects.get(id=class_id)
    user = models.User.objects.get(id=user_id)
    assignment = models.Assignment.objects.get(id=assignment_id)

    return render_template(
            '/administration/classes/show-user-assignment.html',
            class_=class_,
            user=user,
            assignment=assignment)


@module.route('/<class_id>/activities/<activity_id>/users')
# @acl.allows.requires(acl.is_class_owner)
def list_activity_users(class_id, activity_id):
    class_ = models.Class.objects.get(id=class_id)
    activity = models.Activity.objects.get(id=activity_id)
    enrollments = class_.get_enrollments()
    users = [e.user for e in enrollments]
    users.sort(key=lambda u: u.first_name)

    return render_template(
            '/administration/classes/list-activity-users.html',
            class_=class_,
            users=users,
            activity=activity)


@module.route('/<class_id>/users/export-attendents')
# @acl.allows.requires(acl.is_class_owner)
def export_attendants(class_id):
    class_ = models.Class.objects.get(id=class_id)
    
    activities = models.Activity.objects(class_=class_).order_by('started_date')

    sheet1_header = ['Student ID',
              'First Name',
              'Last Name',
              'Section',
              ]

    sheet2_header = sheet1_header[:]

    for activity in activities:
        sheet1_header.append(activity.name)

    for role in class_.student_roles:
        sheet2_header.append(role)

    sheet1_row_list = []
    sheet2_row_list = []

    for section, sids in class_.limited_enrollment.items():
        for sid in sids:
            user = models.User.objects(username=sid).first()

            sheet1_data = {
                    'Student ID': sid,
                    'First Name': user.metadata.get(
                        'thai_first_name', user.first_name) if user else '',
                    'Last Name': user.metadata.get(
                        'thai_last_name', user.last_name) if user else '',
                    'Section': section,
                }

            sheet2_data = sheet1_data.copy()
            for role in class_.student_roles:
                sheet2_data[role] = 0

            for activity in activities:
                ap = None
                if user:
                    ap = activity.get_participator_info(user)
                if ap:
                    sheet1_data[activity.name] = 1
                    for role in ap.student_roles:
                        sheet2_data[role] += 1
                
                else:
                    sheet1_data[activity.name] = 0
            

            sheet1_row_list.append(sheet1_data)
            sheet2_row_list.append(sheet2_data)

    df = pandas.DataFrame(sheet1_row_list)
    df.index += 1
    output = io.BytesIO()
    writer = pandas.ExcelWriter(output, engine='xlsxwriter')
    df.to_excel(writer, sheet_name='Attendant')
    
    df2 = pandas.DataFrame(sheet2_row_list)
    df2.index += 1
    df2.to_excel(writer, sheet_name='Role')

    writer.save()

    return Response(
            output.getvalue(),
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            headers={
                'Content-disposition': f'attachment; filename*=UTF-8\'\'{quote(activity.name.encode("utf-8"))}.xlsx'}
            )


@module.route('/<class_id>/users/export-scores')
# @acl.allows.requires(acl.is_class_owner)
def export_scores(class_id):
    class_ = models.Class.objects.get(id=class_id)
    enrollments = models.Enrollment.objects(enrolled_class=class_)
    users = [e.user for e in enrollments]
    users.sort(key=lambda u: u.username)


    assignments = []
    for ass_time in class_.assignment_schedule:
        assignments.append(ass_time.assignment)

    assignments.sort(key=lambda ass: ass.name)

    header = ['id', 'name', 'lastname']
    subheader = ['no', '', '']

    total_score = 0
    for ass in assignments:
        header.append(ass.name)
        subheader.append(ass.score)
        total_score += ass.score
    header.append('total')
    subheader.append(total_score)

    output =  io.StringIO()
    writer = csv.writer(output)

    writer.writerow(header)
    writer.writerow(subheader)
    for user in users:
        total_score = 0

        sid = user.metadata.get('student_id')
        data = []
        if sid:
            data.append(sid)
        else:
            data.append(user.username)

        if user.metadata.get('thai_first_name'):
            data.append(user.metadata.get('thai_first_name'))
        else:
            data.append(user.first_name)

        if user.metadata.get('thai_last_name'):
            data.append(user.metadata.get('thai_last_name'))
        else:
            data.append(user.last_name)

        for ass in assignments:
            score = ass.get_score(class_, user)
            data.append(score)
            total_score += score
        data.append(total_score)
        writer.writerow(data)

    return Response(output.getvalue(),
                    mimetype='text/csv',
                    headers={
                        'Content-disposition':
                        f'attachment; filename={class_.id}-scores.csv'
    				})


@module.route('/<class_id>/add-user/<user_id>')
# @acl.allows.requires(acl.is_class_owner)
def add_user_to_class(class_id, user_id):
    class_ = models.Class.objects.get(id=class_id)
    user = models.User.objects.get(id=user_id)

    user.enroll(class_)
    return redirect(request.referrer)



@module.route('/<class_id>/teaching-assistants/add', methods=['GET', 'POST'])
# @acl.allows.requires(acl.is_class_owner)
def add_teaching_assistant(class_id):
    class_ = models.Class.objects().get(id=class_id)
    users = models.User.objects().order_by('first_name')

    form = forms.classes.TeachingAssistantAddingForm()
    form.users.choices = [(str(user.id),
                           '{} {} ({}, {})'.format(
                               user.first_name,
                               user.last_name,
                               user.username,
                               user.email)) for user in users]

    if not form.validate_on_submit():
        return render_template(
                '/administration/classes/add-teaching-assistant.html',
                form=form,
                class_=class_,
                users=users)

    for user_id in form.users.data:
        user = models.User.objects.get(id=user_id)

        found_user = False
        for ta in class_.teaching_assistants:
            if ta.user == user:
                found_user = True
                break

        if not found_user:
            ta = models.TeachingAssistant(
                    user=user,
                    ended_date=class_.ended_date
                    )
            class_.teaching_assistants.append(ta)
    class_.save()

    return redirect(url_for('administration.classes.view', class_id=class_id))
