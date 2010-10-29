# -*- coding: utf-8 -*-
"""
Exceptions used by django-rules. All internal and rules-specific errors
should extend RulesError class
"""

class RulesError(Exception):
    pass

class NonexistentPermission(RulesError):
    pass

class NonexistentFieldName(RulesError):
    pass

class NotBooleanPermission(RulesError):
    pass
