from flask import (
    Blueprint,
    render_template,
    url_for,
    redirect,
    current_app,
    session,
    request,
)
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash

from vidya import models
from .. import forms
from .. import oauth2
import datetime

module = Blueprint("accounts", __name__)


def get_user_and_remember():
    client = oauth2.oauth2_client
    result = client.principal.get("me")
    data = result.json()

    user = models.User.objects(
        me.Q(username=data.get("username", "")) | me.Q(email=data.get("email", ""))
    ).first()
    if not user:
        user = models.User(
            id=data.get("id"),
            first_name=data.get("first_name").title(),
            last_name=data.get("last_name").title(),
            email=data.get("email"),
            username=data.get("username"),
            status="active",
        )
        roles = []
        for role in ["student", "lecturer", "staff"]:
            if role in data.get("roles", []):
                roles.append(role)

        user.save()

    if user:
        login_user(user, remember=True)


@module.route("/login", methods=("GET", "POST"))
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    if "next" in request.args:
        session["next"] = request.args.get("next", None)

    return render_template("/accounts/login.html")


@module.route("/login/<name>")
def login_oauth(name):
    client = oauth2.oauth2_client

    scheme = request.environ.get("HTTP_X_FORWARDED_PROTO", "http")
    redirect_uri = url_for(
        "accounts.authorized_oauth", name=name, _external=True, _scheme=scheme
    )
    response = None
    if name == "google":
        response = client.google.authorize_redirect(redirect_uri)
    elif name == "facebook":
        response = client.facebook.authorize_redirect(redirect_uri)
    elif name == "line":
        response = client.line.authorize_redirect(redirect_uri)

    elif name == "psu":
        response = client.psu.authorize_redirect(redirect_uri)
    elif name == "engpsu":
        response = client.engpsu.authorize_redirect(redirect_uri)
    return response


@module.route("/auth/<name>")
def authorized_oauth(name):
    client = oauth2.oauth2_client
    remote = None
    try:
        if name == "google":
            remote = client.google
        elif name == "facebook":
            remote = client.facebook
        elif name == "line":
            remote = client.line
        elif name == "psu":
            remote = client.psu
        elif name == "engpsu":
            remote = client.engpsu

        token = remote.authorize_access_token()

    except Exception as e:
        print("autorize access error =>", e)
        return redirect(url_for("accounts.login"))

    session["oauth_provider"] = name
    return oauth2.handle_authorized_oauth2(remote, token)


@module.route("/logout")
@login_required
def logout():
    name = session.get("oauth_provider")
    logout_user()
    session.clear()

    client = oauth2.oauth2_client
    remote = None
    logout_url = None
    if name == "google":
        remote = client.google
        logout_url = f"{ remote.server_metadata.get('end_session_endpoint') }?redirect={ request.scheme }://{ request.host }"
    elif name == "facebook":
        remote = client.facebook
    elif name == "line":
        remote = client.line
    elif name == "psu":
        remote = client.psu
        logout_url = f"{ remote.server_metadata.get('end_session_endpoint') }?redirect={ request.scheme }://{ request.host }"
    elif name == "engpsu":
        remote = client.engpsu

    if logout_url:
        return redirect(logout_url)

    return redirect(url_for("site.index"))


@module.route("/accounts")
@login_required
def index():
    return render_template("/accounts/index.html")


@module.route("/accounts/edit-profile", methods=["GET", "POST"])
@login_required
def edit_profile():
    form = forms.accounts.Profile(
        obj=current_user,
    )
    if not form.validate_on_submit():
        return render_template("/accounts/edit-profile.html", form=form)

    user = current_user._get_current_object()
    user.first_name = form.first_name.data
    user.last_name = form.last_name.data
    user.organization = form.organization.data

    user.save()

    return redirect(url_for("accounts.index"))


@module.route("/login-engpsu")
def login_engpsu():
    client = oauth2.oauth2_client
    redirect_uri = url_for("accounts.authorized_engpsu", _external=True)
    response = client.engpsu.authorize_redirect(redirect_uri)
    return response


@module.route("/authorized-engpsu")
def authorized_engpsu():
    client = oauth2.oauth2_client
    try:
        token = client.engpsu.authorize_access_token()
    except Exception as e:
        print(e)
        return redirect(url_for("accounts.login"))

    userinfo_response = client.engpsu.get("userinfo")
    userinfo = userinfo_response.json()

    user = models.User.objects(username=userinfo.get("username")).first()

    if not user:
        user = models.User(
            username=userinfo.get("username"),
            email=userinfo.get("email"),
            first_name=userinfo.get("first_name"),
            last_name=userinfo.get("last_name"),
            status="active",
        )
        user.resources[client.engpsu.name] = userinfo
        # if 'staff_id' in userinfo.keys():
        #     user.roles.append('staff')
        # elif 'student_id' in userinfo.keys():
        #     user.roles.append('student')
        if userinfo["username"].isdigit():
            user.roles.append("student")
        else:
            user.roles.append("staff")

        user.save()

    login_user(user)

    oauth2token = models.OAuth2Token(
        name=client.engpsu.name,
        user=user,
        access_token=token.get("access_token"),
        token_type=token.get("token_type"),
        refresh_token=token.get("refresh_token", None),
        expires=datetime.datetime.fromtimestamp(token.get("expires_in")),
    )
    oauth2token.save()
    identity_changed.send(
        current_app._get_current_object(), identity=Identity(user.roles)
    )

    next_uri = session.get("next", url_for("dashboard.index"))

    return redirect(next_uri)
