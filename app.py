from flask import Flask, request, redirect, url_for
import os
import requests
from decimal import Decimal
from models import db, Account, Transaction
from seed import get_db_uri, seed_db
from routes import web, api

app = Flask(__name__)

app.secret_key = os.environ.get('SECRET_KEY', 'bank_secret_key')

app.config['SQLALCHEMY_DATABASE_URI'] = get_db_uri()
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
    app.run(host="0.0.0.0", port=5000)