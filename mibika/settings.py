import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get(
    'DJANGO_SECRET_KEY',
    'django-insecure-q8n#9k_l5v@2m3p&8x-9z$0a!1b@2c#3d$4e%5f^6g&7h*8i(9j)0k-1l_2m+3n',
)

DEBUG = os.environ.get('DJANGO_DEBUG', 'True').lower() in ('1', 'true', 'yes')

ALLOWED_HOSTS = ['localhost', '127.0.0.1', '*.localhost', '0.0.0.0', 'testserver']


# ─────────────────────────────────────────
#  APPLICATIONS
# ─────────────────────────────────────────

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third party
    'rest_framework',
    'rest_framework.authtoken',
    'corsheaders',

# Nos apps Mi-bika
     'users',
     'wardrobe',
     'outfits',
     'weather',
     'events',
     'trends',
     'ratings',
     'feedback',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.middleware.gzip.GZipMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'mibika.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'mibika.wsgi.application'


# ─────────────────────────────────────────
#  BASE DE DONNÉES — NE PAS MODIFIER
# ─────────────────────────────────────────

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'Mi-bika'),
        'USER': os.environ.get('DB_USER', 'esn_user'),
        'PASSWORD': os.environ.get('DB_PASSWORD', '123mibika'),
        'HOST': os.environ.get('DB_HOST', '127.0.0.1'),
        'PORT': os.environ.get('DB_PORT', '5432'),
    }
}

# Override database for testing if needed
import sys
if 'test' in sys.argv or 'test_coverage' in sys.argv:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'test_db.sqlite3',
        }
    }


# ─────────────────────────────────────────
#  AUTHENTIFICATION
# ─────────────────────────────────────────

AUTH_USER_MODEL = 'users.Utilisateur'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Mots de passe chiffrés avec bcrypt (cahier des charges §10)
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.BCryptSHA256PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
]

JWT_ACCESS_MINUTES = int(os.environ.get('JWT_ACCESS_MINUTES', '60'))
JWT_REFRESH_DAYS = int(os.environ.get('JWT_REFRESH_DAYS', '7'))

# ─────────────────────────────────────────
#  DJANGO REST FRAMEWORK — AJOUTÉ
# ─────────────────────────────────────────

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'users.authentication.JWTAuthentication',
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}


# ─────────────────────────────────────────
#  INTERNATIONALISATION
# ─────────────────────────────────────────

LANGUAGE_CODE = 'fr-fr'
TIME_ZONE     = 'Indian/Antananarivo'  # ← CORRIGÉ pour Madagascar
USE_I18N      = True
USE_TZ        = True

# Langues supportées : Français et Malgache
LANGUAGES = [
    ('fr', 'Français'),
    ('mg', 'Malagasy'),
]

# Répertoire des fichiers de traduction
LOCALE_PATHS = [
    BASE_DIR / 'locale',
]


# ─────────────────────────────────────────
#  FICHIERS STATIQUES
# ─────────────────────────────────────────

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'  # collectstatic output (production)
STATICFILES_DIRS = [BASE_DIR / 'static']

# ─────────────────────────────────────────
#  APIS EXTERNES
# ─────────────────────────────────────────

# Open-Meteo — météo open-source, sans clé API
OPENMETEO_FORECAST_URL = os.environ.get(
    'OPENMETEO_FORECAST_URL', 'https://api.open-meteo.com/v1/forecast'
)
OPENMETEO_GEOCODING_URL = os.environ.get(
    'OPENMETEO_GEOCODING_URL', 'https://geocoding-api.open-meteo.com/v1/search'
)

# Firebase Cloud Messaging (notifications push — BF9)
FCM_SERVER_KEY = os.environ.get('FCM_SERVER_KEY', '')

# CORS — frontend Vue.js (Vite dev + production)
CORS_ALLOWED_ORIGINS = [
    'http://localhost:5173',
    'http://127.0.0.1:5173',
    'http://localhost:4173',
    'http://127.0.0.1:4173',
]
CORS_ALLOW_CREDENTIALS = True