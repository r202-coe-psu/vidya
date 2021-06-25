from flask import Blueprint, render_template
from flask_login import login_required

from . import activities
from . import classes
from . import users

module = Blueprint('administration',
                   __name__,
                   url_prefix='/administration')
views = [
        activities,
        classes,
        users,
        ]

@module.route('/')
@login_required
def index():
    return render_template('/dashboard/index.html')
