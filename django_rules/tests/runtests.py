#!/usr/bin/env python
# -*- coding: utf-8 -*-


import os
import sys

os.environ['DJANGO_SETTINGS_MODULE'] = 'test_settings'
parent = os.path.dirname(os.path.dirname(os.path.dirname(
            os.path.abspath(__file__))))

sys.path.insert(0, parent)

from django.test.simple import DjangoTestSuiteRunner



def runtests():
    DjangoTestSuiteRunner(failfast=False).run_tests([
        'django_rules.BackendTest',
        'django_rules.RulePermissionTest',
        'django_rules.UtilsTest',
        'django_rules.DecoratorsTest'
    ], verbosity=1, interactive=True)

if __name__ == '__main__':
    runtests()
