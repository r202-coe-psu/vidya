from flask import redirect, url_for, request
from flask_login import LoginManager, current_user, login_url
from flask_principal import (Principal,
                             Permission,
                             RoleNeed,
                             UserNeed,
							 identity_loaded,
                             )

from functools import wraps

from .. import models

login_manager = LoginManager()
principals = Principal()

admin_permission = Permission(RoleNeed('admin'))
lecturer_permission = Permission(RoleNeed('lecturer'))
supervisor_permission = Permission(RoleNeed('supervisor'))
admin_or_supervisor_permission = Permission(
        RoleNeed('admin'), RoleNeed('supervisor'))

def init_acl(app):
    # initial login manager
    login_manager.init_app(app)
    principals.init_app(app)


def roles_requred(roles):
    def wrapper(func):
        @wraps(func)
        def wrapped(*args, **kwargs):
            for role in roles:
                if role in current_user.roles:
                    return func(*args, **kwargs)
            raise Forbidden()

        return wrapped

    return wrapper



@login_manager.user_loader
def load_user(user_id):
    user = models.User.objects.with_id(user_id)
    return user


@login_manager.unauthorized_handler
def unauthorized_callback():
    if request.method == 'GET':
        response = redirect(login_url('accounts.login',
                                      request.url))
        return response

    return redirect(url_for('accounts.login'))

@identity_loaded.connect
def on_identity_loaded(sender, identity):
    # Set the identity user object
    identity.user = current_user

    # Add the UserNeed to the identity
    if hasattr(current_user, 'id'):
        identity.provides.add(UserNeed(current_user.id))

    # Assuming the User model has a list of roles, update the
    # identity with the roles that the user provides
    if hasattr(current_user, 'roles'):
        for role in current_user.roles:
            identity.provides.add(RoleNeed(role))

