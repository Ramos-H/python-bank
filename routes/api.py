from flask import request, redirect, url_for, Blueprint, session, flash, current_app
import os
import requests
from decimal import Decimal
from models import db, Account, Transaction
import qrcode
from pathlib import Path

api_routes = Blueprint('api_routes', __name__)


@api_routes.route("/health")
def health():
    try:
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
        flash("Missing payment details.", "danger")
        return redirect(url_for("web_routes.payment_done"))

    try:
        amount = Decimal(amount_str)
    except Exception:
        flash("Invalid payment amount format.", "danger")
        return redirect(url_for("web_routes.payment_done"))

    # Enforce bank login — if not logged in, redirect to login then back to confirmation
    if "user" not in session:
        next_url = url_for(
            'web_routes.confirmation',
            order_id=order_id,
            amount=amount_str,
            merchant_account=merchant_account
        )
        flash("Please log in to confirm your payment.", "warning")
        return redirect(url_for("web_routes.login", next=next_url))

    user_name = session["user"]

    # Record transaction (balance deduction skipped until full auth is wired)
    try:
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
        current_app.logger.error(f"Transaction DB Error: {str(e)}")

    # Notify ecommerce that this order is now PAID
    callback_url = current_app.config.get('ECOMMERCE_CALLBACK_URL', 'http://localhost:5000/callback/payment-status')
    try:
        payload = {
            "order_id": order_id,
            "status": "PAID",
            "reference_number": f"TXN-{tx.id}",
            "amount": float(amount)
        }
        resp = requests.post(callback_url, json=payload, timeout=5)
        current_app.logger.info(f"Callback returned {resp.status_code}")
    except Exception as e:
        current_app.logger.error(f"Callback error: {e}")

    # Phone sees a clean "payment done" page
    return redirect(url_for('web_routes.payment_done',
                            ref=f"TXN-{tx.id}",
                            order_id=order_id,
                            amount=amount_str))


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

    # Use BANK_PUBLIC_HOST so QR URLs are reachable from phone on the same LAN
    bank_public_host = current_app.config.get('BANK_PUBLIC_HOST', 'http://localhost:5001').rstrip('/')

    confirmation_path = url_for(
        'web_routes.confirmation',
        order_id=order_id,
        merchant_account="bloomcart-flowers",
        amount=amount
    )
    qr_target_url = f"{bank_public_host}{confirmation_path}"

    img = qrcode.make(qr_target_url)

    path = Path("static")
    path.mkdir(parents=True, exist_ok=True)

    filename = f"qr-{order_id}.png"
    img.save(f"static/{filename}")

    qr_image_url = f"{bank_public_host}{url_for('static', filename=filename)}"
    return {"url": qr_image_url, "confirmation_url": qr_target_url}, 200


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
        merchant = Account(
            username=None,
            password=None,
            name=merchant_account,
            type="MERCHANT",
            balance=Decimal("0.00")
        )
        db.session.add(merchant)
        db.session.commit()

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
            current_app.logger.info(f"API Callback to {callback_url} returned {resp.status_code}")
        except Exception as e:
            current_app.logger.error(f"API Callback failed: {e}")

    return {
        "status": "success",
        "reference_number": f"TXN-{tx.id}",
        "order_id": order_id,
        "amount": float(amount),
        "merchant_account": merchant_account
    }, 200


@api_routes.route("/login", methods=["POST"])
def process_login():
    username = request.form.get("username", "").strip().lower()
    password = request.form.get("password", "")

    next_url = request.form.get("next") or request.args.get("next")

    # Look up user in the bank DB
    account = Account.query.filter_by(username=username, type='CONSUMER').first()

    if not account:
        flash("Invalid username.", "danger")
        return redirect(url_for("web_routes.login", next=next_url or ""))

    if account.password != password:
        flash("Invalid password.", "danger")
        return redirect(url_for("web_routes.login", next=next_url or ""))

    # Store the account name in session (used by process_payment and dashboard)
    session["user"] = account.name

    # Redirect to next_url if provided (e.g. back to confirmation page after login)
    if next_url:
        return redirect(next_url)

    return redirect(url_for("web_routes.dashboard"))