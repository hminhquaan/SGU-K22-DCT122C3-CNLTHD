from pathlib import Path
import os
import sys

BASE_DIR = Path(__file__).resolve().parent.parent
USE_SQLITE_FOR_TESTS = "test" in sys.argv or os.getenv("DJANGO_USE_SQLITE_FOR_TESTS", "0") == "1"


def load_dotenv_file(dotenv_path: Path) -> None:
    if not dotenv_path.exists():
        return

    for raw_line in dotenv_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


load_dotenv_file(BASE_DIR / ".env")

SECRET_KEY = "django-insecure-change-me"
DEBUG = True
ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = [
    "unfold",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "shop",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "fitness_shop.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "shop.context_processors.cart_count",
            ],
        },
    },
]

WSGI_APPLICATION = "fitness_shop.wsgi.application"
ASGI_APPLICATION = "fitness_shop.asgi.application"

DATABASES = {
    "default": {
        **(
            {
                "ENGINE": "django.db.backends.sqlite3",
                "NAME": BASE_DIR / "test_db.sqlite3",
            }
            if USE_SQLITE_FOR_TESTS
            else {
                "ENGINE": "django.db.backends.mysql",
                "NAME": os.getenv("MYSQL_DATABASE", "fitness_shop_db"),
                "USER": os.getenv("MYSQL_USER", "root"),
                "PASSWORD": os.getenv("MYSQL_PASSWORD", ""),
                "HOST": os.getenv("MYSQL_HOST", "127.0.0.1"),
                "PORT": os.getenv("MYSQL_PORT", "3306"),
                "OPTIONS": {
                    "charset": "utf8mb4",
                    "connect_timeout": 5,
                },
                "CONN_MAX_AGE": 0,
            }
        ),
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "vi-vn"
TIME_ZONE = "Asia/Ho_Chi_Minh"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"
VNPAY_URL = os.getenv("VNPAY_URL", "https://sandbox.vnpayment.vn/paymentv2/vpcpay.html")
VNPAY_TMN_CODE = os.getenv("VNPAY_TMN_CODE", "")
VNPAY_HASH_SECRET = os.getenv("VNPAY_HASH_SECRET", "")
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY", "")
LOGIN_URL = "/login/"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

UNFOLD = {
    "SITE_TITLE": "ZENITH FITNESS",
    "SITE_HEADER": "ZENITH FITNESS",
    "SITE_SUBHEADER": "Quản trị bán hàng",
    "SITE_URL": "/",
    "STYLES": [
        "unfold/zenith.css",
    ],
}
