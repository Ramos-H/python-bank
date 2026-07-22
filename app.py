from flask import Flask
from flask import render_template

app = Flask(__name__)

@app.route("/health")
def health():
    return {'status': 'ok'}, 200


@app.route("/dashboard")
def dashboard():
    return render_template(
        "dashboard.html",
        user_name="John Doe",
        available_balance="25,000.00",
        pending_balance="2,500.00",
        total_balance="27,500.00",
        transactions=[
            {
                "date": "2026-07-22",
                "description": "Payment Received",
                "amount": "1,000.00",
                "status": "Completed"
            }
        ]
    )

@app.route("/confirmation")
def confirmation():
    order = {
        "id": "ORD-10001",
        "description": "Premium Subscription",
        "subtotal": 49.99,
        "fee": 2.50,
        "total": 52.49
    }

    payment = {
        "method": "Credit Card",
        "masked_account": "**** **** **** 1234"
    }

    return render_template(
        "confirmation.html",
        order=order,
        payment=payment
    )

@app.route("/confirmed")
def confirmed():
    return render_template(
        "confirmed.html",
        reference_number="TXN-20260722-001",
        amount="5,000.00",
        recipient="ABC Services",
        payment_date="July 22, 2026",
        payment_method="Bank Transfer"
    )