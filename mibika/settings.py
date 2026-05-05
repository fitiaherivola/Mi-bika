from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-q8n#9k_l5v@2m3p&8x-9z$0a!1b@2c#3d$4e%5f^6g&7h*8i(9j)0k-1l_2m+3n'

DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1', '*.localhost']


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
    'rest_framework.authtoken',  # ← AJOUTÉ

    # Nos apps Mi-bika
    'users',
    'wardrobe',
    'outfits',
    'weather',
    'events',
    'trends',
    'ratings',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
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
        'NAME': 'Mi-bika',
        'USER': 'esn_user',
        'PASSWORD': '123mibika',
        'HOST': '127.0.0.1',
        'PORT': '5432',
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

# ─────────────────────────────────────────
#  DJANGO REST FRAMEWORK — AJOUTÉ
# ─────────────────────────────────────────

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}


# ─────────────────────────────────────────
#  INTERNATIONALISATION
# ─────────────────────────────────────────

LANGUAGE_CODE = 'fr-fr'
TIME_ZONE     = 'Indian/Antananarivo'  # ← CORRIGÉ pour Madagascar
USE_I18N      = True
USE_TZ        = True


# ─────────────────────────────────────────
#  FICHIERS STATIQUES
# ─────────────────────────────────────────

STATIC_URL    = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'