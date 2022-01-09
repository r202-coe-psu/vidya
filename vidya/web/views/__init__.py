import datetime

from . import site
from . import accounts
from . import dashboard
from . import classes
from . import activities
from . import attendances

from . import teaching_assistants

from . import admin
from . import administration


def add_date_url(url):
    now = datetime.datetime.now()
    return f'{url}?date={now.strftime("%Y%m%d")}'


def get_subblueprints(views=[]):
    blueprints = []
    for view in views:
        blueprints.append(view.module)
        if "views" in dir(view):
            for module in get_subblueprints(view.views):
                view.module.register_blueprint(module)
    return blueprints


def register_blueprint(app):
    app.add_template_filter(add_date_url)
    blueprints = get_subblueprints(
        [
            site,
            accounts,
            dashboard,
            classes,
            activities,
            attendances,
            teaching_assistants,
            administration,
            admin,
        ]
    )

    for blueprint in blueprints:
        app.register_blueprint(blueprint)
