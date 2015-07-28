from flask import Flask
from profapp.controllers.blueprints import user_bp, article_bp, filemanager_bp
import profapp.controllers.views_article as views_art
import profapp.controllers.views_auth as views_auth
import profapp.controllers.views_filemanager as views_fileman
import profapp.controllers.views_index as views_ind

def create_app(config='config.ProductionDevelopmentConfig'):
    app = Flask(__name__)
    app.config.from_object(config)

    app.register_blueprint(views_ind.general_bp, url_prefix='/')
    app.register_blueprint(views_art.article_bp, url_prefix='/articles')
    app.register_blueprint(views_auth.user_bp, url_prefix='/users')
    app.register_blueprint(views_fileman.filemanager_bp, url_prefix='/filemanager')
    app.register_blueprint(views_fileman.static_bp, url_prefix='/static')

    from db_init import db_session

    # see: http://flask.pocoo.org/docs/0.10/patterns/sqlalchemy/
    # Flask will automatically remove database sessions at the end of the request
    # or when the application shuts down:
    @app.teardown_appcontext
    def shutdown_session(exception=None):
        db_session.remove()

    return app
