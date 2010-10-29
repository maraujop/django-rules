import os

BASE_DIR = os.path.dirname(__file__)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.sessions',
    'django.contrib.contenttypes',
    'django.contrib.admin',
    'django_rules',
    'django_rules.tests',
    )

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
    }
}

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'django_rules.backends.ObjectPermissionBackend',
)

ANONYMOUS_USER_ID = '1'
