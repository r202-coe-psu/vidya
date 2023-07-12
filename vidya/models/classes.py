import mongoengine as me
import datetime


class Enrollment(me.Document):
    user = me.ReferenceField("User", dbref=True, required=True)
    enrolled_class = me.ReferenceField("Class", dbref=True, required=True)
    enrolled_date = me.DateTimeField(required=True, default=datetime.datetime.now)

    meta = {"collection": "enrollments"}


class LimitedEnrollment(me.EmbeddedDocument):
    section = me.StringField(required=True)
    grantees = me.ListField(me.StringField(required=True))
    updated_date = me.DateTimeField(
        required=True, auto_now=True, default=datetime.datetime.now
    )


class AssignmentTime(me.EmbeddedDocument):
    assignment = me.ReferenceField("Assignment", required=True)
    started_date = me.DateTimeField(required=True, default=datetime.datetime.now)
    ended_date = me.DateTimeField(required=True, default=datetime.datetime.now)
    updated_date = me.DateTimeField(
        required=True, auto_now=True, default=datetime.datetime.now
    )


class TeachingAssistant(me.EmbeddedDocument):
    user = me.ReferenceField("User", dbref=True, required=True)
    started_date = me.DateTimeField(required=True, default=datetime.datetime.now)
    ended_date = me.DateTimeField(required=True, default=datetime.datetime.now)
    updated_date = me.DateTimeField(
        required=True, auto_now=True, default=datetime.datetime.now
    )


class Class(me.Document):
    name = me.StringField(required=True)
    description = me.StringField(required=True)
    code = me.StringField()
    # course = me.ReferenceField('Course', required=True)
    # assignment_schedule = me.ListField(
    #         me.EmbeddedDocumentField(AssignmentTime))
    tags = me.ListField(me.StringField(required=True))

    created_date = me.DateTimeField(
        required=True,
        default=datetime.datetime.now,
    )
    updated_date = me.DateTimeField(
        required=True,
        default=datetime.datetime.now,
        auto_now=True,
    )

    limited_enrollment = me.DictField()

    # limited = me.BooleanField(required=True, default=False)
    # enrollments = me.ListField(me.ReferenceField('Enrollment', dbref=True))
    started_date = me.DateTimeField(required=True, default=datetime.datetime.now)

    ended_date = me.DateTimeField(required=True, default=datetime.datetime.now)

    owner = me.ReferenceField("User", dbref=True, required=True)
    # teaching_assistants = me.ListField(
    #         me.EmbeddedDocumentField(TeachingAssistant))
    contributors = me.ListField(me.ReferenceField("User", dbref=True, required=True))

    sections = me.ListField(me.StringField(required=True))
    student_roles = me.ListField(me.StringField(required=True))
    score_items = me.DictField(default={})

    meta = {
        "collection": "classes",
    }

    def get_enrollments(self):
        return Enrollment.objects(enrolled_class=self).all()

    def get_section(self, user):
        for k, v in self.limited_enrollment.items():
            if user.username in v:
                return k

    def is_teaching_assistant(self, user):
        for ta in self.teaching_assistants:
            if user == ta.user:
                return True

        return False

    def get_assignment_score(self, user):
        total_assignment_score = 0
        total_assignment_user_score = 0
        for ass_t in self.assignment_schedule:
            assignment = ass_t.assignment
            total_assignment_score += assignment.score
            total_assignment_user_score += assignment.get_score(self, user)

        return dict(
            total_score=total_assignment_score,
            total_user_score=total_assignment_user_score,
        )

    def get_assignment_schedule(self, assignment):
        ass_time = None
        for ass in self.assignment_schedule:
            if ass.assignment == assignment:
                ass_time = ass
                break

        return ass_time

    def is_enrolled(self, user_id=None, user=None):
        from .users import User

        if user_id:
            user = User.objects.get(id=user_id)
            if not user:
                return False

        if user:
            enrollment = Enrollment.objects(user=user, enrolled_class=self).first()
            if enrollment:
                return True

        return False

    def get_enrolled_information(self, user_id):
        for e in self.get_enrollments():
            if str(user_id) == str(e.user.id):
                return e

        return None

    def get_total_attendee_score(self, user):
        from .attendances import Attendance, Attendee

        attendances = Attendance.objects(class_=self)
        total_score = 0
        for attendance in attendances:
            attendee = Attendee.objects(user=user, attendance=attendance).first()
            if not attendee:
                continue

            total_score += attendance.score
            for role in attendee.student_roles:
                total_score += self.score_items.get(role, 0)

        return total_score

    def get_attendee_score_by_attendance(self, user, attendance):
        total_score = attendance.score
        attendee = Attendee.objects(user=user, attendance=attendance).first()
        if not attendee:
            return total_score

        for role in attendee.student_roles:
            total_score += self.score_items.get(role, 0)

        return total_score

    def get_attendee_score(self, attendee):
        attendance = attendee.attendance
        total_score = attendance.score
        if not attendee:
            return total_score

        for role in attendee.student_roles:
            total_score += self.score_items.get(role, 0)

        return total_score
