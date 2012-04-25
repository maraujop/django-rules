# -*- coding: utf-8 -*-


import inspect

from django.conf import settings
from django.utils.importlib import import_module

from django_rules import mem_store
from exceptions import (
    NotBooleanPermission,
    NonexistentFieldName,
    RulesError,
)


class ObjectPermissionBackend(object):
    supports_object_permissions = True
    supports_anonymous_user = True
    supports_inactive_user = True

    def authenticate(self, username, password):  # pragma: no cover
        return None

    def has_perm(self, user_obj, perm, obj=None):
        """
        This method checks if the user_obj has perm on obj. Returns True or False
        Looks for the rule with the code_name = perm and the content_type of the obj
        If it exists returns the value of obj.field_name or obj.field_name() in case
        the field is a method.
        """
        if obj is None:
            return False

        # Centralized authorizations: You need to define a module in settings.CENTRAL_AUTHORIZATIONS that has a 
        # central_authorizations function inside
        if hasattr(settings, 'CENTRAL_AUTHORIZATIONS'):
            module = getattr(settings, 'CENTRAL_AUTHORIZATIONS')

            try:
                mod = import_module(module)
            except ImportError, e:
                raise RulesError('Error importing central authorizations module %s: "%s"' % (module, e))

            try:
                central_authorizations = getattr(mod, 'central_authorizations')
            except AttributeError:
                raise RulesError("Error module %s does not have a central_authorization function" % (module))

            try:
                is_authorized = central_authorizations(user_obj, perm)
                # If the value returned is a boolean we pass it up and stop checking
                # If not, we continue checking
                if isinstance(is_authorized, bool):
                    return is_authorized

            except TypeError:
                raise RulesError('central_authorizations should receive 2 parameters: (user_obj, perm)')

        # We get the rule for that perm
        # If the rule doesn't exist, return False for Django authorization cascading
        rule = mem_store.get(perm, obj.__class__)
        if rule is None:
            return False

        bound_field = getattr(obj, rule.field_name)

        if not isinstance(bound_field, bool) and not callable(bound_field) and bound_field is not None:
            raise NotBooleanPermission("Attribute %s from model %s on rule %s does not return a boolean value",
                                        (rule.field_name, obj.__class__, rule.codename))

        if not callable(bound_field):
            is_authorized = bound_field
        else:
            # Otherwise it is a callabe bound_field
            # Let's see if we pass or not user_obj as a parameter
            if (len(inspect.getargspec(bound_field)[0]) == 2):
                is_authorized = bound_field(user_obj)
            else:
                is_authorized = bound_field()

            if not isinstance(is_authorized, bool):
                raise NotBooleanPermission("Callable %s from model %s on rule %s does not return a boolean value",
                                            (rule.field_name, rule.ModelType, rule.codename))

        return is_authorized
