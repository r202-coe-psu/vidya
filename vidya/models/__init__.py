from . import users
from . import oauth2
from . import classes
from . import attendances

from .users import User
from .oauth2 import OAuth2Token
from .classes import (
    Class,
    Enrollment,
    LimitedEnrollment,
    AssignmentTime,
    TeachingAssistant,
)
from .attendances import Attendance, Attendee

__all__ = [
    users,
    User,
    oauth2,
    OAuth2Token,
    classes,
    Class,
    Enrollment,
    LimitedEnrollment,
    AssignmentTime,
    TeachingAssistant,
    Attendance,
    Attendee,
]


from flask_mongoengine import MongoEngine

db = MongoEngine()


def init_db(app):
    db.init_app(app)


def init_mongoengine(settings):
    import mongoengine as me

    dbname = settings.get("MONGODB_DB")
    host = settings.get("MONGODB_HOST", "localhost")
    port = int(settings.get("MONGODB_PORT", "27017"))
    username = settings.get("MONGODB_USERNAME", "")
    password = settings.get("MONGODB_PASSWORD", "")

    me.connect(db=dbname, host=host, port=port, username=username, password=password)
