import os
from pathlib import Path
from typing import Any, Dict

repo_dir = Path(__file__).resolve().parent

def _build_db_uri() -> str:
    if os.environ.get('FLASK_ENV') == 'testing':
        return 'sqlite:///:memory:'

    if os.environ.get('USE_SQLITE', 'false').lower() == 'true':
        return f"sqlite:///{(repo_dir / 'bank.db').as_posix()}"

    db_user = os.environ.get('DB_USER', 'root')
    db_password = os.environ.get('DB_PASSWORD', 'rootpassword')
    db_host = os.environ.get('DB_HOST', 'localhost')
    db_port = os.environ.get('DB_PORT', '3306')
    db_name = os.environ.get('DB_NAME', 'banking')

    return f"mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

vars: Dict[str, Any] = {
    'APP_HOSTNAME': os.environ.get('APP_HOSTNAME','http://localhost'),
    'APP_PORT': os.environ.get('APP_PORT', 5001),
    'FLASK_ENV': os.environ.get('FLASK_ENV'),
    'USE_SQLITE': os.environ.get('USE_SQLITE', 'false').lower(),
    'DB_USER': os.environ.get('DB_USER', 'root'),
    'DB_PASSWORD': os.environ.get('DB_PASSWORD', 'rootpassword'),
    'DB_HOST': os.environ.get('DB_HOST', 'localhost'),
    'DB_PORT': os.environ.get('DB_PORT', 3306),
    'DB_NAME': os.environ.get('DB_NAME', 'banking'),
    'SECRET_KEY': os.environ.get('SECRET_KEY', 'bank_secret_key'),
    # Public hostname used in QR codes — must be reachable from phone (LAN IP or ngrok URL)
    'BANK_PUBLIC_HOST': os.environ.get('BANK_PUBLIC_HOST', 'http://10.55.16.108:5001'),
    # Ecommerce callback — bank calls this after payment; use LAN IP so it works from same machine
    'ECOMMERCE_CALLBACK_URL': os.environ.get('ECOMMERCE_CALLBACK_URL', 'http://10.55.16.108:5000/callback/payment-status'),
    'SQLALCHEMY_DATABASE_URI': _build_db_uri(),
}