from flask import Blueprint

from vidya.web import acl

module = Blueprint("admin", __name__, url_prefix="/admin")


@module.route("/")
@acl.roles_required("admin")
def index():
    return "admin"
