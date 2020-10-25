from flask import Flask, g
import os
from .extensions import db, migrate, flask_static_digest, assets_env

def create_app():
    app = Flask(
        __name__,
        static_folder='assets',
        static_url_path='/assets/'
    )

    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI') or os.getenv('POSTGRESQL_ADDON_URI')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
    app.config['ASSETS_DEBUG'] = True

    db.init_app(app)
    migrate.init_app(app, db)
    flask_static_digest.init_app(app)
    assets_env.init_app(app)

    with app.app_context():
        from .inscription import models, blueprint as inscription_bp
        from .recommandations import models, commands, blueprint as recommandation_bp
        from .avis import models, commands, blueprint as avis_bp
        from .stats import blueprint as stats_bp
        from .newsletter import blueprint as newsletter_bp
        from .pages import blueprint as pages_bp

        app.register_blueprint(inscription_bp.bp)
        app.register_blueprint(stats_bp.bp)
        app.register_blueprint(avis_bp.bp)
        app.register_blueprint(recommandation_bp.bp)
        app.register_blueprint(newsletter_bp.bp)
        app.register_blueprint(pages_bp.bp)

        app.jinja_env.add_extension("ecosante.utils.rollup.RollupJSExtension")
        app.jinja_env.add_extension("ecosante.utils.rollup.SCSSExtension")

    return app