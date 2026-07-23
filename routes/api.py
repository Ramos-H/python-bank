from flask import request, redirect, url_for, Blueprint, session, flash
import os
import requests
from decimal import Decimal
from models import db, Account, Transaction
<<<<<<< HEAD
import random
=======
>>>>>>> c83b028 (Fixed Error Redirect in dashboard for Confirm Payment)
import qrcode
from pathlib import Path

api_routes = Blueprint('api_routes', __name__)

<<<<<<< HEAD
@api_routes.route("/health")
def health():
    try:
        # Simple query to check DB connection
=======

@api_routes.route("/health")
def health():
    try:
>>>>>>> c83b028 (Fixed Error Redirect in dashboard for Confirm Payment)
        db.session.execute(db.text("SELECT 1"))
        return {'status': 'ok', 'database': 'connected'}, 200
    except Exception as e:
        return {'status': 'error', 'reason': str(e)}, 500

<<<<<<< HEAD
=======

>>>>>>> c83b028 (Fixed Error Redirect in dashboard for Confirm Payment)
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

    if "user" not in session:
        return redirect(url_for("web_routes.login"))

    user_name = session["user"]
<<<<<<< HEAD
    
=======

>>>>>>> c83b028 (Fixed Error Redirect in dashboard for Confirm Payment)
    customer = Account.query.filter_by(name=user_name, type='CONSUMER').first()
    merchant = Account.query.filter_by(name=merchant_account, type='MERCHANT').first()

    if not customer:
        return "Customer account not found", 404
    if not merchant:
        return f"Merchant account '{merchant_account}' not found", 404
    if customer.balance < amount:
        return "Insufficient funds", 400

    try:
<<<<<<< HEAD
        # Perform the transfer
        customer.balance -= amount
        merchant.balance += amount

        # Record the transaction
=======
        customer.balance -= amount
        merchant.balance += amount

>>>>>>> c83b028 (Fixed Error Redirect in dashboard for Confirm Payment)
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

<<<<<<< HEAD
    # Call back the e-commerce app to mark PAID
=======
>>>>>>> c83b028 (Fixed Error Redirect in dashboard for Confirm Payment)
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

<<<<<<< HEAD
    return redirect(url_for('web_routes.confirmed', 
                            ref=f"TXN-{tx.id}", 
                            amount=amount_str, 
                            recipient=merchant_account,
                            date=tx.timestamp.strftime("%B %d, %Y")))

=======
    return redirect(url_for('web_routes.confirmed',
                            ref=f"TXN-{tx.id}",
                            amount=amount_str,
                            recipient=merchant_account,
                            date=tx.timestamp.strftime("%B %d, %Y")))


>>>>>>> c83b028 (Fixed Error Redirect in dashboard for Confirm Payment)
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
<<<<<<< HEAD
    
    if order_id is None:
        return {'error': 'order_id not given.'}, 422
    
    if amount is None:
        return {'error': 'amount not given.'}, 422

    # hostname="http://127.0.0.1:5001"
    hostname="http://10.91.102.74:5001"
=======

    if order_id is None:
        return {'error': 'order_id not given.'}, 422

    if amount is None:
        return {'error': 'amount not given.'}, 422

    hostname = "http://10.91.102.74:5001"
>>>>>>> c83b028 (Fixed Error Redirect in dashboard for Confirm Payment)

    result = url_for('web_routes.confirmation', order_id=order_id, merchant_account="bloomcart-flowers", amount=amount)
    img = qrcode.make(f"{hostname}{result}")

    path = Path("static")
<<<<<<< HEAD

    path.mkdir(parents=True, exist_ok=True)

    filename=f"qr-{order_id}.png"
=======
    path.mkdir(parents=True, exist_ok=True)

    filename = f"qr-{order_id}.png"
>>>>>>> c83b028 (Fixed Error Redirect in dashboard for Confirm Payment)
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
    customer_account = session.get("user")

    if not customer_account:
        return {
            "status": "error",
            "message": "User not logged in"
        }, 401

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
<<<<<<< HEAD

    username = request.form.get("username", "").lower()
    password = request.form.get("password", "")

    # Demo users
=======
    username = request.form.get("username", "").lower()
    password = request.form.get("password", "")

    # Capture next target from request form OR request query parameters
    next_url = request.form.get("next") or request.args.get("next")

>>>>>>> c83b028 (Fixed Error Redirect in dashboard for Confirm Payment)
    users = {
        "maria": {
            "password": "password123",
            "account_name": "Maria Makiling"
        },
        "pedro": {
            "password": "password123",
            "account_name": "Pedro Penduko"
        }
    }

    user = users.get(username)

    if not user:
        flash("Invalid username.", "danger")
<<<<<<< HEAD
        return redirect(url_for("web_routes.login"))

    if password != user["password"]:
        flash("Invalid password.", "danger")
        return redirect(url_for("web_routes.login"))

    # Save logged-in user
    session["user"] = user["account_name"]

    if "pending_order" in session:
        order = session.pop("pending_order")

    return redirect(
        url_for(
            "web_routes.confirmation",
            order_id=order["order_id"],
            amount=order["amount"],
            merchant_account=order["merchant_account"]
        )
    )

=======
        return redirect(url_for("web_routes.login", next=next_url if next_url else None))

    if password != user["password"]:
        flash("Invalid password.", "danger")
        return redirect(url_for("web_routes.login", next=next_url if next_url else None))

    # Save user to session
    session["user"] = user["account_name"]

    # --- REDIRECT PRIORITY ---

    # 1. Direct explicit 'next' parameter URL
    if next_url:
        session.pop("next_url", None)
        session.pop("pending_order", None)
        return redirect(next_url)

    # 2. Saved 'next_url' in session
    if "next_url" in session:
        target = session.pop("next_url")
        session.pop("pending_order", None)
        return redirect(target)

    # 3. Saved 'pending_order' parameters in session
    if "pending_order" in session:
        order = session.pop("pending_order")
        return redirect(
            url_for(
                "web_routes.confirmation",
                order_id=order["order_id"],
                amount=order["amount"],
                merchant_account=order["merchant_account"]
            )
        )

    # 4. Standard default dashboard redirect
>>>>>>> c83b028 (Fixed Error Redirect in dashboard for Confirm Payment)
    return redirect(url_for("web_routes.dashboard"))