# -*- coding: utf-8 -*-
import inspect

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User, AnonymousUser
from django.utils.importlib import import_module

from models import RulePermission
from exceptions import NotBooleanPermission
from exceptions import NonexistentFieldName
from exceptions import NonexistentPermission
from exceptions import RulesError


class ObjectPermissionBackend(object):
    supports_object_permissions = True
    supports_anonymous_user = True

    def authenticate(self, username, password):
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

        if not user_obj.is_authenticated():
            user_obj = User.objects.get(pk=settings.ANONYMOUS_USER_ID)

        # Centralized authorizations
        # You need to define a module in settings.CENTRAL_AUTHORIZATIONS that has a 
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
                raise RulesError('Error module %s does not have a central_authorization function"' % (module))
            
            try:
                value = central_authorizations(user_obj, perm)
                if not isinstance(value, bool):
                    raise NotBooleanPermission("central_authorizations did not return a boolean value")

            except TypeError:
                raise RulesError('central_authorizations should receive 2 parameters: (user_obj, perm)')

        # Note:
        # is_active and is_superuser are checked by default in django.contrib.auth.models
        # lines from 301-306 in Django 1.2.3
        # So we don't double check, If this changes tests will catch it
        ctype = ContentType.objects.get_for_model(obj)

        # We get the rule data and return the value of that rule
        try:
            rule = RulePermission.objects.get(codename = perm, content_type = ctype)
        except RulePermission.DoesNotExist:
            raise NonexistentPermission('RulePermission with codename %s on model %s does not exist',
                                        (perm, ctype.model))

        bound_field = None
        try:
            bound_field = getattr(obj, rule.field_name)
        except AttributeError:
            raise NonexistentFieldName("Field_name %s from rule %s does not longer exist in model %s. \
                                        The rule is obsolete!", (rule.field_name, rule.codename, rule.content_type.model))

        if not isinstance(bound_field, bool) and not callable(bound_field):
            raise NotBooleanPermission("Attribute %s from model %s on rule %s does not return a boolean value",
                                        (rule.field_name, rule.content_type.model, rule.codename))

        if not callable(bound_field):
            return bound_field

        # Otherwise it is a callabe bound_field
        # Let's see if we pass or not user_obj as a parameter
        if (len(inspect.getargspec(bound_field)[0]) == 2):
            value = bound_field(user_obj)
        else:
            value = bound_field()

        if not isinstance(value, bool):
            raise NotBooleanPermission("Callable %s from model %s on rule %s does not return a boolean value",
                                        (rule.field_name, rule.content_type.model, rule.codename))

        return value
