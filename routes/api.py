from flask import request, redirect, url_for, Blueprint
import os
import requests
from decimal import Decimal
from models import db, Account, Transaction
import random
import qrcode
from pathlib import Path

api_routes = Blueprint('api_routes', __name__)

@api_routes.route("/health")
def health():
    try:
        # Simple query to check DB connection
        db.session.execute(db.text("SELECT 1"))
        return {'status': 'ok', 'database': 'connected'}, 200
    except Exception as e:
        return {'status': 'error', 'reason': str(e)}, 500

@api_routes.route("/confirmation", methods=["POST"])
def process_payment():
    order_id = request.form.get('order_id')
    amount_str = request.form.get('amount')
    merchant_account = request.form.get('merchant_account')

    if not order_id or not amount_str or not merchant_account:
        return "Missing payment details", 400

    try:
        amount = Decimal(amount_str)
    except Exception:
        return "Invalid amount", 400

    user_name = "Maria Makiling"
    
    customer = Account.query.filter_by(name=user_name, type='CONSUMER').first()
    merchant = Account.query.filter_by(name=merchant_account, type='MERCHANT').first()

    if not customer:
        return "Customer account not found", 404
    if not merchant:
        return f"Merchant account '{merchant_account}' not found", 404
    if customer.balance < amount:
        return "Insufficient funds", 400

    try:
        # Perform the transfer
        customer.balance -= amount
        merchant.balance += amount

        # Record the transaction
        tx = Transaction(
            order_id=order_id,
            from_acct=user_name,
            to_acct=merchant_account,
            amount=amount
        )
        db.session.add(tx)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return f"Database error: {str(e)}", 500

    # Call back the e-commerce app to mark PAID
    callback_url = os.environ.get('ECOMMERCE_CALLBACK_URL')
    if callback_url:
        try:
            payload = {
                "order_id": order_id,
                "status": "PAID",
                "reference_number": f"TXN-{tx.id}",
                "amount": float(amount)
            }
            resp = requests.post(callback_url, json=payload, timeout=5)
            api_routes.logger.info(f"Callback to {callback_url} returned {resp.status_code}")
        except Exception as e:
            api_routes.logger.error(f"Failed to trigger callback to e-commerce app: {e}")

    return redirect(url_for('web_routes.confirmed', 
                            ref=f"TXN-{tx.id}", 
                            amount=amount_str, 
                            recipient=merchant_account,
                            date=tx.timestamp.strftime("%B %d, %Y")))

@api_routes.route("/get-payment-link", methods=["POST"])
def get_qr_url():
    if request.is_json:
        data = request.get_json()
    else:
        data = request.form

    order_id = data.get("order_id")
    amount = data.get("amount")

    if order_id is None and amount is None:
        return {'error': 'order_id and amount not given.'}, 422
    
    if order_id is None:
        return {'error': 'order_id not given.'}, 422
    
    if amount is None:
        return {'error': 'amount not given.'}, 422

    hostname="http://127.0.0.1:5000"
    result = url_for('web_routes.confirmation', order_id=order_id, merchant_account="bloomcart-flowers", amount=amount)
    img = qrcode.make(f"{hostname}{result}")

    path = Path("static")

    path.mkdir(parents=True, exist_ok=True)

    filename=f"qr-{order_id}.png"
    img.save(f"static/{filename}")
    return {"url": f"{hostname}{url_for('static', filename=filename)}"}, 200


@api_routes.route("/pay", methods=["POST"])
def pay_api():
    if request.is_json:
        data = request.get_json()
    else:
        data = request.form

    order_id = data.get('order_id')
    amount_str = data.get('amount')
    merchant_account = data.get('merchant_account')
    customer_account = data.get('customer_account', 'Maria Makiling')

    if not order_id or not amount_str or not merchant_account:
        return {"status": "error", "message": "Missing required parameters"}, 400

    try:
        amount = Decimal(str(amount_str))
    except Exception:
        return {"status": "error", "message": "Invalid amount format"}, 400

    customer = Account.query.filter_by(name=customer_account, type='CONSUMER').first()
    merchant = Account.query.filter_by(name=merchant_account, type='MERCHANT').first()

    if not customer:
        return {"status": "error", "message": f"Customer account '{customer_account}' not found"}, 404
    if not merchant:
        return {"status": "error", "message": f"Merchant account '{merchant_account}' not found"}, 404
    if customer.balance < amount:
        return {"status": "error", "message": "Insufficient funds"}, 400

    try:
        customer.balance -= amount
        merchant.balance += amount

        tx = Transaction(
            order_id=order_id,
            from_acct=customer_account,
            to_acct=merchant_account,
            amount=amount
        )
        db.session.add(tx)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return {"status": "error", "message": f"Database error: {str(e)}"}, 500

    callback_url = os.environ.get('ECOMMERCE_CALLBACK_URL')
    if callback_url:
        try:
            payload = {
                "order_id": order_id,
                "status": "PAID",
                "reference_number": f"TXN-{tx.id}",
                "amount": float(amount)
            }
            resp = requests.post(callback_url, json=payload, timeout=5)
            api_routes.logger.info(f"API Callback to {callback_url} returned {resp.status_code}")
        except Exception as e:
            api_routes.logger.error(f"API Callback failed: {e}")

    return {
        "status": "success",
        "reference_number": f"TXN-{tx.id}",
        "order_id": order_id,
        "amount": float(amount),
        "merchant_account": merchant_account
    }, 200


@api_routes.route("/login", methods=["POST"])
def process_login():
    username = request.form.get("username")
    password = request.form.get("password")

    # auth logic here

    return redirect(url_for("web_routes.dashboard"))