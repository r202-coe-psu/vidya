from flask import (Blueprint,
                   render_template,
                   request,
                   redirect,
                   url_for)

from flask_login import current_user, login_required

from vidya.web import acl, forms
from vidya import models

subviews = []

module = Blueprint('administration.activities',
                   __name__,
                   url_prefix='/activities',
                   )


@module.route('/')
@acl.allows.requires(acl.is_lecturer)
def index():
    activities = models.Activity.objects(
            owner=current_user._get_current_object())
    return render_template('/administration/activities/index.html',
                           activities=activities)


@module.route('/create', methods=['GET', 'POST'])
@acl.allows.requires(acl.is_lecturer)
def create():
    class_ = models.Class.objects.get(id=request.args.get('class_id', ''))
    if not class_:
        return 'Class not found'

    form = forms.activities.ActivityForm()
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
@acl.allows.requires(acl.is_lecturer)
def edit(activity_id):
    class_ = models.Class.objects.get(id=request.args.get('class_id', ''))
    if not class_:
        return 'Class not found'

    activity = models.Activity.objects.get(id=activity_id)

    form = forms.activities.ActivityForm(obj=activity)
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




@module.route('/<activity_id>/delete')
@acl.allows.requires(acl.is_lecturer)
def delete(activity_id):
    activity = models.Activity.objects.get(id=activity_id)
    course = activity.course
    course.activities.remove(activity)
    course.save()

    activity.delete()


    return redirect(url_for('administration.courses.view',
                            course_id=course.id))


@module.route('/<activity_id>/add-challenges', methods=['GET', 'POST'])
@acl.allows.requires(acl.is_lecturer)
def add_challenge(activity_id):
    activity = models.Activity.objects.get(id=activity_id)
    
    challenges = models.Challenge.objects()
    choices = [(str(q.id), q.name) for q in challenges \
            if q not in activity.challenges]
    form = forms.activities.ChallengeAddingForm()
    form.challenges.choices = choices

    if not form.validate_on_submit():
        return render_template('/administration/activities/view.html',
                               activity=activity,
                               form=form)
    challenge_ids = form.challenges.data.copy()

    for challenge_id in challenge_ids:
        challenge = models.Challenge.objects.get(id=challenge_id)
        if challenge in activity.challenges:
            continue

        activity.challenges.append(challenge)

    activity.save()
    return redirect(url_for('administration.activities.view',
                            activity_id=activity.id))

@module.route('/<activity_id>')
@acl.allows.requires(acl.is_lecturer)
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
@acl.allows.requires(acl.is_lecturer)
def list_participators(activity_id):
    activity = models.Activity.objects.get(id=activity_id)
    participators = models.ActivityParticipator.objects(activity=activity)

    participators = sorted(participators, key=lambda p: p.section)


    return render_template('/administration/activities/list-participators.html',
                           activity=activity,
                           participators=participators,
                           )

@module.route('/<activity_id>/map/<section>')
@login_required
@acl.allows.requires(acl.is_lecturer)
def show_map(activity_id, section):
    activity = models.Activity.objects.get(id=activity_id)

    participators = []
    if section == 'all':
        participators = models.ActivityParticipator.objects(activity=activity)
    else:
        participators = models.ActivityParticipator.objects(activity=activity, section=section)

    data = participators.to_json().replace('\"', '\\"')
    return render_template('/administration/activities/show_map.html',
                           activity=activity,
                           participators=participators,
                           data=data,
                           )

