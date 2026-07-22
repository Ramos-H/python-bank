from flask_sqlalchemy import SQLAlchemy
import datetime

db = SQLAlchemy()

class Account(db.Model):
    __tablename__ = 'accounts'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), unique=True, nullable=False, index=True)
    type = db.Column(db.String(20), nullable=False)  # CONSUMER or MERCHANT
    balance = db.Column(db.Numeric(15, 2), nullable=False, default=0.00)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'type': self.type,
            'balance': float(self.balance)
        }

class Transaction(db.Model):
    __tablename__ = 'transactions'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    order_id = db.Column(db.String(100), nullable=False, index=True)
    from_acct = db.Column(db.String(100), nullable=False)
    to_acct = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Numeric(15, 2), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'order_id': self.order_id,
            'from_acct': self.from_acct,
            'to_acct': self.to_acct,
            'amount': float(self.amount),
            'timestamp': self.timestamp.isoformat()
        }
