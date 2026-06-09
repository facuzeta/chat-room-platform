import os
from email.utils import formataddr
from pathlib import Path
import environ

BASE_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = BASE_DIR.parent

for env_file in (REPO_ROOT / ".env", BASE_DIR / ".env"):
    if env_file.exists():
        environ.Env.read_env(env_file)

env = environ.Env(
    DEBUG=(bool, False),
    SECURE_SSL_REDIRECT=(bool, False),
    USE_REDIS=(bool, False),
    ENABLE_SCREENER_SYNC=(bool, True),
    EMAIL_PORT=(int, 1025),
    EMAIL_USE_TLS=(bool, False),
    EMAIL_USE_SSL=(bool, False),
)

ENV_BEANSTALK = "RDS_PORT" in os.environ
DEBUG = env.bool("DEBUG", default=not ENV_BEANSTALK)
SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=ENV_BEANSTALK)
SECURE_REDIRECT_EXEMPT = [r"^no-ssl/$", r"^no-ssl$"] if SECURE_SSL_REDIRECT else []


def env_word_list(name, default):
    raw_value = env(name, default="")
    if not raw_value:
        return default
    return raw_value.replace(",", " ").split()


SECRET_KEY = env("SECRET_KEY")
ALLOWED_HOSTS = env_word_list("ALLOWED_HOSTS", ["127.0.0.1", "localhost"])
CSRF_TRUSTED_ORIGINS = env_word_list("CSRF_TRUSTED_ORIGINS", [])
DOMAIN = env("DOMAIN", default="http://127.0.0.1:8000")
ENABLE_SCREENER_SYNC = env.bool("ENABLE_SCREENER_SYNC", default=True)


INSTALLED_APPS = [
    "channels",
    "chat",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "group_manager",
    "django_extensions",
    "cms",
    "external_raters",
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

ROOT_URLCONF = "mysite.urls"

template_dirs = [os.path.join(BASE_DIR, "templates")]
if ENV_BEANSTALK:
    template_dirs.append("/var/app/current/templates")

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": template_dirs,
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "mysite.wsgi.application"

database_url = env("DATABASE_URL", default="")
if database_url:
    DATABASES = {"default": env.db("DATABASE_URL")}
elif ENV_BEANSTALK:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql_psycopg2",
            "NAME": os.environ["RDS_DB_NAME"],
            "USER": os.environ["RDS_USERNAME"],
            "PASSWORD": os.environ["RDS_PASSWORD"],
            "HOST": os.environ["RDS_HOSTNAME"],
            "PORT": os.environ["RDS_PORT"],
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

LANGUAGE_CODE = "es-ar"
TIME_ZONE = "America/Argentina/Buenos_Aires"

USE_I18N = True
USE_L10N = True
USE_TZ = True

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
ASGI_APPLICATION = "mysite.asgi.application"

REDIS_URL = env("REDIS_URL", default="")
USE_REDIS = env.bool("USE_REDIS", default=ENV_BEANSTALK or bool(REDIS_URL))
if USE_REDIS:
    CHANNEL_LAYERS = {
        "default": {
            "BACKEND": "channels_redis.core.RedisChannelLayer",
            "CONFIG": {"hosts": [REDIS_URL or "redis://127.0.0.1:6379/0"]},
        }
    }
else:
    CHANNEL_LAYERS = {"default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}}

EMAIL_BACKEND = env(
    "EMAIL_BACKEND",
    default="django.core.mail.backends.smtp.EmailBackend",
)
EMAIL_HOST = env("EMAIL_HOST", default="localhost")
EMAIL_PORT = env.int("EMAIL_PORT", default=1025)
EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")
EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=False)
EMAIL_USE_SSL = env.bool("EMAIL_USE_SSL", default=False)
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="no-reply@local.test")
EMAIL_FROM_NAME = env("EMAIL_FROM_NAME", default="NeuroExp Local")
EMAIL_ADDRESS = formataddr((EMAIL_FROM_NAME, DEFAULT_FROM_EMAIL))

STATIC_URL = "/static/"
STATIC_ROOT = env("STATIC_ROOT", default=str(BASE_DIR / "staticfiles"))
if not ENV_BEANSTALK:
    STATICFILES_DIRS = [
        BASE_DIR / "static",
    ]

LOGIN_URL = "/login"
