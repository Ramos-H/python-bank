import os
import pytest
from decimal import Decimal

# Set test environment variables before importing app
os.environ['FLASK_ENV'] = 'testing'
os.environ['USE_SQLITE'] = 'true'

from app import app, db
from models import Account, Transaction
from seed import seed_db

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            seed_db(app)
        yield client
        with app.app_context():
            db.drop_all()

def test_health_check(client):
    response = client.get('/health')
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data['status'] == 'ok'
    assert json_data['database'] == 'connected'

def test_dashboard_seeded(client):
    response = client.get('/dashboard')
    assert response.status_code == 200
    assert b"Maria Makiling" in response.data
    assert b"50,000.00" in response.data

def test_payment_confirmation_get(client):
    response = client.get('/confirmation?order_id=ORD-99&amount=250.00&merchant_account=sweetcrumb-pastries')
    assert response.status_code == 200
    assert b"ORD-99" in response.data
    assert b"250.00" in response.data
    assert b"sweetcrumb-pastries" in response.data

def test_payment_confirmation_post(client):
    with app.app_context():
        customer = Account.query.filter_by(name="Maria Makiling").first()
        initial_balance = customer.balance

    response = client.post('/confirmation', data={
        'order_id': 'ORD-99',
        'amount': '250.00',
        'merchant_account': 'sweetcrumb-pastries'
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b"Payment Successful" in response.data
    assert b"TXN-" in response.data
    
    with app.app_context():
        customer = Account.query.filter_by(name="Maria Makiling").first()
        merchant = Account.query.filter_by(name="sweetcrumb-pastries").first()
        tx = Transaction.query.filter_by(order_id="ORD-99").first()
        
        assert customer.balance == initial_balance - Decimal("250.00")
        assert merchant.balance == Decimal("250.00")
        assert tx is not None
        assert tx.amount == Decimal("250.00")

def test_pay_api(client):
    with app.app_context():
        customer = Account.query.filter_by(name="Maria Makiling").first()
        initial_balance = customer.balance

    response = client.post('/pay', json={
        'order_id': 'ORD-100',
        'amount': '150.50',
        'merchant_account': 'sweetcrumb-pastries'
    })

    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data['status'] == 'success'
    assert 'reference_number' in json_data
    
    with app.app_context():
        customer = Account.query.filter_by(name="Maria Makiling").first()
        merchant = Account.query.filter_by(name="sweetcrumb-pastries").first()
        assert customer.balance == initial_balance - Decimal("150.50")
        assert merchant.balance == Decimal("150.50")
