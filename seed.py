import os
from flask import Flask
from models import db, Account
from decimal import Decimal

def get_db_uri():
    db_user = os.environ.get('DB_USER', 'root')
    db_password = os.environ.get('DB_PASSWORD', 'rootpassword')
    db_host = os.environ.get('DB_HOST', 'localhost')
    db_port = os.environ.get('DB_PORT', '3306')
    db_name = os.environ.get('DB_NAME', 'banking')

    # Support SQLite for local/test run if specified
    if os.environ.get('FLASK_ENV') == 'testing' or os.environ.get('USE_SQLITE', 'false').lower() == 'true':
        if os.environ.get('FLASK_ENV') == 'testing':
            return 'sqlite:///:memory:'
        return 'sqlite:///C:/Users/HRR83780/OneDrive - EastWest Banking Corporation/Documents/python-bank/bank.db'

    return f"mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

def seed_db(app=None):
    if app is None:
        app = Flask(__name__)
        app.config['SQLALCHEMY_DATABASE_URI'] = get_db_uri()
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        db.init_app(app)

    with app.app_context():
        print("Creating database tables if they do not exist...")
        db.create_all()

        print("Seeding default accounts...")

        # Consumer accounts — same credentials as ecommerce so users can log in with either app
        consumers = [
            {
                "username": "john",
                "password": "password123",
                "name": "John Doe",
                "balance": Decimal("50000.00")
            },
            {
                "username": "jane",
                "password": "password123",
                "name": "Jane Smith",
                "balance": Decimal("50000.00")
            },
            {
                "username": "alice",
                "password": "password123",
                "name": "Alice Johnson",
                "balance": Decimal("50000.00")
            }
        ]

        for c in consumers:
            acc = Account.query.filter_by(username=c["username"]).first()

            if not acc:
                acc = Account(
                    username=c["username"],
                    password=c["password"],
                    name=c["name"],
                    type="CONSUMER",
                    balance=c["balance"]
                )
                db.session.add(acc)
                print(f"Added consumer account: {c['name']} with balance {c['balance']}")
            else:
                print(f"Consumer account {c['name']} already exists.")

        # Merchant accounts
        merchants = [
            {"name": "sweetcrumb-pastries"},
            {"name": "freshmart-groceries"},
            {"name": "pageturn-books"},
            {"name": "bloomcart-flowers"},
            {"name": "brewhouse-coffee"}
        ]
        for m in merchants:
            acc = Account.query.filter_by(name=m["name"]).first()
            if not acc:
                acc = Account(
                    username=None,
                    password=None,
                    name=m["name"],
                    type="MERCHANT",
                    balance=Decimal("0.00")
                )
                db.session.add(acc)
                print(f"Added merchant account: {m['name']}")
            else:
                print(f"Merchant account {m['name']} already exists.")

        db.session.commit()
        print("Seeding complete.")

if __name__ == "__main__":
    seed_db()