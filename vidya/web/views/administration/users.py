from flask import (Blueprint,
                   render_template,
                   url_for,
                   redirect
                   )
from flask_login import current_user

from vidya.web import acl, forms
from vidya import models

module = Blueprint('users',
                   __name__,
                   url_prefix='/users',
                   )


@module.route('/')
@acl.admin_permission.require(http_exception=403)
def index():
    users = models.User.objects().order_by('-id')
    return render_template('/administration/users/index.html',
                           users=users)
