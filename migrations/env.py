import logging
from logging.config import fileConfig
from flask import Flask, current_app
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from alembic import context

# Initialize Flask app
app = Flask(__name__)

# Flask configuration (Example, adjust as needed)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cafe_app.db'  # or any other database URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Blueprint imports
from yourmodule.auth import auth  # Replace with actual import
from yourmodule.products import products_blueprint  # Replace with actual import

# Register Blueprints
app.register_blueprint(auth, url_prefix='/auth')  # Blueprint registration for auth
app.register_blueprint(products_blueprint, url_prefix='/products')  # Blueprint registration for products

# Alembic configuration setup
config = context.config
fileConfig(config.config_file_name)
logger = logging.getLogger('alembic.env')

def get_engine():
    try:
        # This works with Flask-SQLAlchemy < 3 and Alchemical
        return current_app.extensions['migrate'].db.get_engine()
    except (TypeError, AttributeError):
        # This works with Flask-SQLAlchemy >= 3
        return current_app.extensions['migrate'].db.engine

def get_engine_url():
    try:
        return get_engine().url.render_as_string(hide_password=False).replace('%', '%%')
    except AttributeError:
        return str(get_engine().url).replace('%', '%%')

config.set_main_option('sqlalchemy.url', get_engine_url())
target_db = current_app.extensions['migrate'].db

def get_metadata():
    if hasattr(target_db, 'metadatas'):
        return target_db.metadatas[None]
    return target_db.metadata

def run_migrations_offline():
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url, target_metadata=get_metadata(), literal_binds=True
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    """Run migrations in 'online' mode."""
    def process_revision_directives(context, revision, directives):
        if getattr(config.cmd_opts, 'autogenerate', False):
            script = directives[0]
            if script.upgrade_ops.is_empty():
                directives[:] = []
                logger.info('No changes in schema detected.')

    conf_args = current_app.extensions['migrate'].configure_args
    if conf_args.get("process_revision_directives") is None:
        conf_args["process_revision_directives"] = process_revision_directives

    connectable = get_engine()

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=get_metadata(),
            **conf_args
        )

        with context.begin_transaction():
            context.run_migrations()

# Run migrations based on the mode (offline or online)
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

# Run Flask app
if __name__ == '__main__':
    app.run(debug=True)
