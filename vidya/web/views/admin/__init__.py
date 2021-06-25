from flask import Blueprint

from vidya.web import acl

module = Blueprint('admin', __name__, url_prefix='/admin')



@module.route('/')
@acl.admin_permission.require(http_exception=403)
def index():
    return 'admin'
