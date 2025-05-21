import os

from flask import Flask
from flask_bootstrap import Bootstrap4
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

database = SQLAlchemy()
migrate = Migrate()

def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'db.sqlite'),
        UPLOAD_FOLDER = app.instance_path,
        ALLOWED_EXTENSIONS = {'txt','csv'},
        TEMPLATE_AUTO_RELOAD = True,
        SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(app.instance_path, 'db.sqlite'),
        SQLALCHEMY_TRACK_MODIFICATIONS = False,
    )

    database.init_app(app)
    migrate.init_app(app, database)
    
    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass
    
    from . import db
    db.init_app(app)

    from . import category
    app.register_blueprint(category.bp)

    from . import transactions
    app.register_blueprint(transactions.bp)

    from . import home
    app.register_blueprint(home.bp)

    from . import asset
    app.register_blueprint(asset.bp)

    Bootstrap4(app)

    return app