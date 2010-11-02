# -*- coding: utf-8 -*-
import sys, os
import imp
from optparse import make_option

from django.conf import settings
from django.utils.importlib import import_module
from django.core.management import call_command
from django.core.management import BaseCommand
from django.db import connections


def import_app(app_label, verbosity):
    # We get the app_path, necessary to use imp module find function
    try:
        app_path = __import__(app_label, {}, {}, [app_label.split('.')[-1]]).__path__
    except AttributeError:
        return
    except ImportError:
        print "Unknown application: %s" % app_label
        print "Stopping synchronization"
        sys.exit(1)
   
    # imp.find_module looks for rules.py within the app
    # It does not import the module, but raises and ImportError
    # if rules.py does not exist, so we continue to next app
    try:
        imp.find_module('rules', app_path)
    except ImportError:
        return

    if verbosity >= 1:
        sys.stderr.write('Syncing rules from %s\n' % app_label)
    
    # Now we import the module, this should bubble up errors
    # if there are any in rules.py Warning the user
    generator = import_module('.rules', app_label)


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option("--fixture", action='store_true', dest="fixture", default=False,
                   help="Generate a fixture of django_rules"),
    )
    help = 'Syncs into database all rules defined in rules.py files'
    args = '[appname ...]'

    def handle(self, *app_labels, **options):
        verbosity = int(options.pop('verbosity', 1))
        fixture = options.pop('fixture')

        if len(app_labels) == 0:
            # We look for a rules.py within every app in INSTALLED_APPS
            # We sync the rules_list against RulePermissions
            for app_label in settings.INSTALLED_APPS:
                import_app(app_label, verbosity)
        else:
            for app_label in app_labels:
                import_app(app_label, verbosity)

        if fixture:
            for alias in connections._connections:
                call_command("dumpdata",
                         'django_rules.rulepermission',
                        **dict(options, verbosity=0, database=alias))
