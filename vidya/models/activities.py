import mongoengine as me
import datetime

from .classes import Class, Enrollment

class ActivityParticipator(me.Document):

    user = me.ReferenceField('User', db_ref=True, required=True)
    activity = me.ReferenceField('Activity', db_ref=True, required=True)
    registration_date = me.DateTimeField(
            required=True,
            auto_now=True,
            default=datetime.datetime.now)
    section = me.StringField(required=True)

    ip_address = me.StringField(required=True)
    location = me.GeoPointField()
    remark = me.StringField()

    data = me.DictField(required=True, default={})

    meta = {'collection': 'activity_participators'}


class Activity(me.Document):
    name = me.StringField(required=True)
    description = me.StringField()
    score = me.IntField(required=True, default=0)
    class_ = me.ReferenceField('Class',
                               dbref=True,
                               required=True)


    started_date = me.DateTimeField()
    ended_date = me.DateTimeField()

    created_date = me.DateTimeField(required=True,
                                    default=datetime.datetime.now)
    updated_date = me.DateTimeField(required=True,
                                    default=datetime.datetime.now,
                                    auto_now=True)

    owner = me.ReferenceField('User', db_ref=True, required=True)



    meta = {'collection': 'activities'}

    def is_action(self, user):
        return False

def get_activity_schedule(user):
    now = datetime.datetime.now()

    available_classes = Class.objects(
            (me.Q(started_date__lte=now) &
                me.Q(ended_date__gte=now))
            ).order_by('ended_date')

    ass_schedule = []
    for class_ in available_classes:
        if not class_.is_enrolled(user.id):
            continue

        for ass_t in class_.assignment_schedule:
            if ass_t.started_date <= now and now < ass_t.ended_date:
                ass_schedule.append(
                        dict(assignment_schedule=ass_t,
                             class_=class_))

    def order_by_ended_date(e):
        return e['assignment_schedule'].ended_date

    ass_schedule.sort(key=order_by_ended_date)
    return ass_schedule


def get_past_activity_schedule(user):
    now = datetime.datetime.now()

    available_classes = Class.objects(
            (me.Q(started_date__lte=now) &
                me.Q(ended_date__gte=now))
            ).order_by('ended_date')


    ass_schedule = []
    for class_ in available_classes:
        if not class_.is_enrolled(user.id):
            continue

        for ass_t in class_.assignment_schedule:
            if now > ass_t.ended_date:
                ass_schedule.append(
                        dict(assignment_schedule=ass_t,
                             class_=class_))

    def order_by_ended_date(e):
        return e['assignment_schedule'].ended_date

    ass_schedule.sort(key=order_by_ended_date)
    return ass_schedule
