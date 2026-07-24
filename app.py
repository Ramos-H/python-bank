from flask import Flask
from models import db
from seed import seed_db
from routes import web, api
import env

app = Flask(__name__)

app.secret_key = env.vars['SECRET_KEY']

app.config['SQLALCHEMY_DATABASE_URI'] = env.vars['SQLALCHEMY_DATABASE_URI']
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['BANK_PUBLIC_HOST'] = env.vars['BANK_PUBLIC_HOST']
app.config['ECOMMERCE_CALLBACK_URL'] = env.vars['ECOMMERCE_CALLBACK_URL']
db.init_app(app)

# Auto seed database on startup (Dev / Test)
with app.app_context():
    try:
        seed_db(app)
    except Exception as e:
        app.logger.error(f"Error seeding database on startup: {e}")

# Register blueprints (register api_routes without /api prefix to match form actions)
app.register_blueprint(web.web_routes)
app.register_blueprint(api.api_routes)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=env.vars['APP_PORT'])