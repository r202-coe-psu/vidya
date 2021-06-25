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

    ip_address = me.StringField(required=True)
    user_agent = me.StringField(default='')
    client = me.StringField(default='')


    location = me.GeoPointField()
    remark = me.StringField()
    roles = me.ListField(me.StringField())
    
    data = me.DictField(required=True, default={})

    meta = {'collection': 'activity_participators'}


class Activity(me.Document):
    name = me.StringField(required=True)
    description = me.StringField()
    score = me.IntField(required=True, default=0)
    sections = me.ListField(me.StringField())
    required_location = me.BooleanField(default=False)
    required_student_roles = me.BooleanField(default=False)

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

    student_roles = me.ListField(me.StringField(), default=[])

    meta = {'collection': 'activities'}

    def is_available(self, user):
        found_user = False
        for k, v in self.class_.limited_enrollment.items():
            if not str(user.id) in v:
                found_user = True
                break
        if not found_user:
            return False

        now = datetime.datetime.now()
        if self.started_date <= now < self.ended_date:
            return True

        return False

    def is_action(self, user):
        participator = ActivityParticipator.objects(
                user=user,
                activity=self,
                )

        if participator:
            return True

        return False

    def get_participator_info(self, user):
        participator = ActivityParticipator.objects(
                user=user,
                activity=self,
                )
        return participator

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
