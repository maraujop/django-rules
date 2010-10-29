# -*- coding: utf-8 -*-
import os
import imp

from django.conf import settings
from django.utils.importlib import import_module
from django.core.management.base import NoArgsCommand

class Command(NoArgsCommand):
    def handle_noargs(self, **options):
        verbosity = int(options.pop('verbosity', 1))

        # We look for a rules.py within every app in INSTALLED_APPS
        # We sync the rules_list against RulePermissions
        for app in settings.INSTALLED_APPS:
            # We get the app_path, necessary to use imp module find function
            try:
                app_path = __import__(app, {}, {}, [app.split('.')[-1]]).__path__
            except AttributeError:
                continue
           
            # imp.find_module looks for rules.py within the app
            # It does not import the module, but raises and ImportError
            # if rules.py does not exist, so we continue to next app
            try:
                imp.find_module('rules', app_path)
            except ImportError:
                continue

            # Now we import the module, this should bubble up errors
            # if there are any in rules.py Warning the user
            generator = import_module('.rules', app)

            if verbosity >= 1:
                print "Syncing rules from %s" % app
