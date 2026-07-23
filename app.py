from flask import Flask, render_template, request, redirect, url_for, flash
import os
import requests
import datetime
from decimal import Decimal
from models import db, Account, Transaction
from seed import get_db_uri, seed_db

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

@app.route("/")
def index():
    return redirect(url_for('dashboard'))

@app.route("/health")
def health():
    try:
        # Simple query to check DB connection
        db.session.execute(db.text("SELECT 1"))
        return {'status': 'ok', 'database': 'connected'}, 200
    except Exception as e:
        return {'status': 'error', 'reason': str(e)}, 500

@app.route("/dashboard")
def dashboard():
    user_name = "Maria Makiling"
    account = Account.query.filter_by(name=user_name, type='CONSUMER').first()
    
    if not account:
        available_balance = "0.00"
        pending_balance = "0.00"
        total_balance = "0.00"
        transactions_list = []
    else:
        available_balance = f"{account.balance:,.2f}"
        pending_balance = "0.00"
        total_balance = f"{account.balance:,.2f}"
        
        txs = Transaction.query.filter(
            (Transaction.from_acct == user_name) | (Transaction.to_acct == user_name)
        ).order_by(Transaction.timestamp.desc()).all()
        
        transactions_list = []
        for tx in txs:
            is_credit = tx.to_acct == user_name
            desc = f"Received from {tx.from_acct}" if is_credit else f"Paid to {tx.to_acct}"
            if tx.order_id:
                desc += f" (Order: {tx.order_id})"
                
            transactions_list.append({
                "date": tx.timestamp.strftime("%Y-%m-%d %H:%M"),
                "description": desc,
                "amount": f"{tx.amount:,.2f}",
                "status": "Completed"
            })
            
    return render_template(
        "dashboard.html",
        user_name=user_name,
        available_balance=available_balance,
        pending_balance=pending_balance,
        total_balance=total_balance,
        transactions=transactions_list
    )

@app.route("/confirmation", methods=["GET"])
def confirmation():
    order_id = request.args.get('order_id', 'ORD-UNKNOWN')
    amount_str = request.args.get('amount', '0.00')
    merchant_account = request.args.get('merchant_account', 'unknown-merchant')

    try:
        amount = float(amount_str)
    except ValueError:
        amount = 0.00

    order = {
        "id": order_id,
        "description": f"Purchase from {merchant_account}",
        "subtotal": amount,
        "fee": 0.00,
        "total": amount
    }

    payment = {
        "method": "MyBank Account Transfer",
        "masked_account": "Maria Makiling (****1234)"
    }

    return render_template(
        "confirmation.html",
        order=order,
        payment=payment,
        merchant_account=merchant_account
    )

@app.route("/confirmation", methods=["POST"])
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
            app.logger.info(f"Callback to {callback_url} returned {resp.status_code}")
        except Exception as e:
            app.logger.error(f"Failed to trigger callback to e-commerce app: {e}")

    return redirect(url_for('confirmed', 
                            ref=f"TXN-{tx.id}", 
                            amount=amount_str, 
                            recipient=merchant_account,
                            date=tx.timestamp.strftime("%B %d, %Y")))

@app.route("/confirmed")
def confirmed():
    ref = request.args.get('ref', 'TXN-UNKNOWN')
    amount = request.args.get('amount', '0.00')
    recipient = request.args.get('recipient', 'Unknown')
    date = request.args.get('date', datetime.datetime.utcnow().strftime("%B %d, %Y"))

    return render_template(
        "confirmed.html",
        reference_number=ref,
        amount=amount,
        recipient=recipient,
        payment_date=date,
        payment_method="Bank Transfer"
    )

@app.route("/pay", methods=["POST"])
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
            app.logger.info(f"API Callback to {callback_url} returned {resp.status_code}")
        except Exception as e:
            app.logger.error(f"API Callback failed: {e}")

    return {
        "status": "success",
        "reference_number": f"TXN-{tx.id}",
        "order_id": order_id,
        "amount": float(amount),
        "merchant_account": merchant_account
    }, 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)