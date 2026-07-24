from flask import Blueprint, render_template, request, redirect, url_for, session, flash
import datetime
from models import Account, Transaction

web_routes = Blueprint('web_routes', __name__)

@web_routes.route("/")
def index():
    return redirect(url_for("web_routes.login"))


@web_routes.route("/login", methods=["GET"])
def login():
    return render_template("login.html")


@web_routes.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("web_routes.login"))

    user_name = session["user"]

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


@web_routes.route("/confirmation", methods=["GET"])
def confirmation():
    order_id = request.args.get('order_id', 'ORD-UNKNOWN')
    amount_str = request.args.get('amount', '0.00')
    merchant_account = request.args.get('merchant_account', 'bloomcart-flowers')
    payer_username = request.args.get('payer_username', '')

    # Require bank login before showing the payment confirmation page
    if "user" not in session:
        next_url = url_for(
            'web_routes.confirmation',
            order_id=order_id,
            amount=amount_str,
            merchant_account=merchant_account,
            payer_username=payer_username
        )
        flash("Please log in with your bank account to proceed.", "warning")
        return redirect(url_for("web_routes.login", next=next_url))

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
        "method": "NorthSouth Account Transfer",
        "masked_account": f"{session['user']} (****1234)"
    }

    return render_template(
        "confirmation.html",
        order=order,
        payment=payment,
        merchant_account=merchant_account,
        payer_username=payer_username
    )


@web_routes.route("/confirmed")
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


@web_routes.route("/payment-done")
def payment_done():
    """Phone sees this page after confirming payment via QR scan.
    The laptop's waiting.html will detect PAID via polling and show success there.
    """
    ref = request.args.get('ref', 'TXN-UNKNOWN')
    order_id = request.args.get('order_id', '')
    amount = request.args.get('amount', '0.00')
    return render_template("payment_done.html", ref=ref, order_id=order_id, amount=amount)