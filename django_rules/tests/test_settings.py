# -*- coding: utf-8 -*-


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

ROOT_URLCONF = 'test_urls'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
    },
    'handlers': {
        'null': {
            'level': 'DEBUG',
            'class': 'django.utils.log.NullHandler',
        },
        'logfile' : {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': 'django_rules.log',
            'formatter': 'simple'
        },
    },

    'loggers': {
        'django': {
            'level': 'DEBUG',
            'handlers': ['null'],
        },
        'django_rules': {
            'level': 'DEBUG',
            'handlers': ['null'],
            'propagate': False
        },
    }
}
