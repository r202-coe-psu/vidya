from flask import Blueprint, render_template
from flask_login import login_required

# from . import assignments
from . import activities
# from . import challenges
from . import courses
from . import classes
from . import users
from . import solutions

module = Blueprint('administration',
                   __name__,
                   url_prefix='/administration')
subviews = [
        activities,
        # challenges,
        courses,
        classes,
        users,
        solutions,
        ]

@module.route('/')
@login_required
def index():
    return render_template('/dashboard/index.html')
