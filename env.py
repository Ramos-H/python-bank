import os
from pathlib import Path
from typing import Any, Dict

repo_dir = Path(__file__).resolve().parent

def _build_db_uri() -> str:
    if os.environ.get('FLASK_ENV') == 'testing':
        return 'sqlite:///:memory:'

<<<<<<< HEAD
    if os.environ.get('USE_SQLITE', False).lower() == 'true':
=======
    if os.environ.get('USE_SQLITE', 'false').lower() == 'true':
>>>>>>> c83b028 (Fixed Error Redirect in dashboard for Confirm Payment)
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
<<<<<<< HEAD
    'USE_SQLITE': os.environ.get('USE_SQLITE', False).lower(),
=======
    'USE_SQLITE': os.environ.get('USE_SQLITE', 'false').lower(),
>>>>>>> c83b028 (Fixed Error Redirect in dashboard for Confirm Payment)
    'DB_USER': os.environ.get('DB_USER', 'root'),
    'DB_PASSWORD': os.environ.get('DB_PASSWORD', 'rootpassword'),
    'DB_HOST': os.environ.get('DB_HOST', 'localhost'),
    'DB_PORT': os.environ.get('DB_PORT', 3306),
    'DB_NAME': os.environ.get('DB_NAME', 'banking'),
    'SECRET_KEY': os.environ.get('SECRET_KEY', 'bank_secret_key'),
    'ECOMMERCE_CALLBACK_URL': os.environ.get('ECOMMERCE_CALLBACK_URL'),
    'SQLALCHEMY_DATABASE_URI': _build_db_uri(),
<<<<<<< HEAD
}

=======
}
>>>>>>> c83b028 (Fixed Error Redirect in dashboard for Confirm Payment)
