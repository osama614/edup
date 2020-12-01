import os
from flask import Flask
from models import setup_db, MyAdminIndexView
from flask_admin import helpers, expose
from .auth import setup_auth
from .admin import manager
from .student import clint
from .teacher import mentor
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration


def create_app():

    app = Flask(__name__)

    sentry_sdk.init(
      dsn="https://2f94f8c3c9ec4f8cbc4c6c0e318aa9ef@o453360.ingest.sentry.io/5442085",
      traces_sample_rate=0.1 ,
      integrations=[FlaskIntegration()],
      send_default_pii=False
    )
    app.config['SECRET_KEY'] = 'asdfghjkl;fghjkl;'
    app.config['JWT_ACCESS_LIFESPAN'] = {'days': 2}
    setup_db(app)
    setup_auth(app)

    app.register_blueprint(manager, url_prefix='/operators')
    app.register_blueprint(clint, url_prefix='/students')
    app.register_blueprint(mentor, url_prefix='/teachers')



    return app

