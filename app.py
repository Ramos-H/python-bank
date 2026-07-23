from flask import Flask
from models import db
from seed import seed_db
from routes import web, api
import env

app = Flask(__name__)

app.secret_key = env.vars['SECRET_KEY']

app.config['SQLALCHEMY_DATABASE_URI'] = env.vars['SQLALCHEMY_DATABASE_URI']
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# Auto seed database on startup (Dev / Test)
with app.app_context():
    try:
        seed_db(app)
    except Exception as e:
        app.logger.error(f"Error seeding database on startup: {e}")

app.register_blueprint(web.web_routes)
app.register_blueprint(api.api_routes, url_prefix="/api")

if __name__ == "__main__":
    app.run(host=env.vars['APP_HOSTNAME'], port=env.vars['APP_PORT'])