# -*- coding: utf-8 -*-
import os
import sys
from cStringIO import StringIO

from django.test import TestCase
from django.contrib.auth.models import User, AnonymousUser
from django.contrib.contenttypes.models import ContentType
from django.conf import settings
from django_rules.exceptions import (
    NonexistentFieldName,
    NotBooleanPermission,
    RulesError,
)
from django_rules.mem_store import register

from models import Dummy


class BackendTest(TestCase):
    def setUp(self):
        # Users
        self.user = User.objects.get_or_create(username='javier', is_active=True)[0]
        self.otherUser = User.objects.get_or_create(username='juan', is_active=True)[0]
        self.superuser = User.objects.get_or_create(username='miguel', is_active=True, is_superuser=True)[0]
        self.not_active_superuser = User.objects.get_or_create(username='rebeca', is_active=False, is_superuser=True)[0]

        # Object
        self.obj = Dummy.objects.get_or_create(supplier=self.user, name='dummy')[0]

        # Rule
        sys.stderr = open(os.devnull, 'w')  # silencing the "overwriting" warning
        register(codename='can_ship', field_name='canShip', ModelType=Dummy, view_param_pk='idDummy',
                                            description="Only supplier have the authorization to ship")
        sys.stderr = sys.__stderr__

    def test_regularuser_has_perm(self):
        self.assertTrue(self.user.has_perm('can_ship', self.obj))

    def test_regularuser_has_not_perm(self):
        self.assertFalse(self.otherUser.has_perm('can_ship', self.obj))

    def test_regularuser_has_property_perm(self):
        """
        Checks that the backend can work with properties
        """
        register(codename='can_trash', field_name='isDisposable', ModelType=Dummy, view_param_pk='idDummy',
                                            description="Checks if a user can trash a package")
        try:
            self.user.has_perm('can_trash', self.obj)
        except:
            self.fail("Something when wrong when checking a property rule")

    def test_superuser_has_perm(self):
        self.assertTrue(self.superuser.has_perm('invented_perm', self.obj))

    def test_object_none(self):
        self.assertFalse(self.user.has_perm('can_ship'))

    def test_anonymous_user(self):
        anonymous_user = AnonymousUser()
        self.assertFalse(anonymous_user.has_perm('can_ship', self.obj))

    def test_not_active_superuser(self):
        self.assertFalse(self.not_active_superuser.has_perm('can_ship', self.obj))

    def test_nonexistent_perm(self):
        self.assertFalse(self.user.has_perm('nonexistent_perm', self.obj))

    def test_nonboolean_attribute(self):
        register(codename='wrong_rule', field_name='name', ModelType=Dummy, view_param_pk='idDummy',
                                            description="Wrong rule. The field_name exists so It is created, but it does not return True or False")

        self.assertRaises(NotBooleanPermission, lambda: self.user.has_perm('wrong_rule', self.obj))

    def test_nonboolean_method(self):
        register(codename='wrong_rule', field_name='methodInteger', ModelType=Dummy, view_param_pk='idDummy',
                                            description="Wrong rule. The field_name exists so It is created, but it does not return True or False")

        self.assertRaises(NotBooleanPermission, lambda: self.user.has_perm('wrong_rule', self.obj))

    def nonexistent_field_name(self):
        # Dinamycally removing canShip from class Dummy to test an already existent rule that doesn't have a valid field_name anymore
        fun = Dummy.canShip
        del Dummy.canShip
        self.assertRaises(NonexistentFieldName, lambda: self.user.has_perm('can_ship', self.obj))
        Dummy.canShip = fun

    def test_has_perm_method_no_parameters(self):
        register(codename='canTrash', field_name='canTrash', ModelType=Dummy, view_param_pk='idDummy',
                                            description="Rule created from a method that gets no parameters")

        self.assertTrue(self.user.has_perm('canTrash', self.obj))

    def test_central_authorizations_right_module_checked_within(self):
        settings.CENTRAL_AUTHORIZATIONS = 'utils'
        self.assertTrue(self.otherUser.has_perm('all_can_pass', self.obj))
        del settings.CENTRAL_AUTHORIZATIONS

    def test_central_authorizations_right_module_passes_over(self):
        settings.CENTRAL_AUTHORIZATIONS = 'utils'
        self.assertFalse(self.otherUser.has_perm('can_ship', self.obj))
        del settings.CENTRAL_AUTHORIZATIONS

    def test_central_authorizations_wrong_module(self):
        settings.CENTRAL_AUTHORIZATIONS = 'noexistent'
        self.assertRaises(RulesError, lambda: self.user.has_perm('can_ship', self.obj))
        del settings.CENTRAL_AUTHORIZATIONS

    def test_central_authorizations_right_module_nonexistent_function(self):
        settings.CENTRAL_AUTHORIZATIONS = 'utils2'
        self.assertRaises(RulesError, lambda: self.user.has_perm('can_ship', self.obj))
        del settings.CENTRAL_AUTHORIZATIONS

    def test_central_authorizations_right_module_wrong_number_parameters(self):
        settings.CENTRAL_AUTHORIZATIONS = 'utils3'
        self.assertRaises(RulesError, lambda: self.user.has_perm('can_ship', self.obj))
        del settings.CENTRAL_AUTHORIZATIONS


class RulePermissionTest(TestCase):
    def setUp(self):
        self.user = User.objects.get_or_create(username='javier', is_active=True)[0]
        self.obj = Dummy.objects.get_or_create(supplier=self.user)[0]
        self.ctype = ContentType.objects.get_for_model(self.obj)

    def test_invalid_field_name(self):
        self.assertRaises(NonexistentFieldName, lambda: register(codename='can_ship', field_name='invalidField', ModelType=Dummy,
                                                                        view_param_pk='idDummy', description="Only supplier have the authorization to ship"))

    def test_valid_attribute(self):
        try:
            register(codename='can_ship', field_name='supplier', ModelType=Dummy, view_param_pk='idDummy', description="Only supplier have the authorization to ship")
        except:
            self.fail('')

    def test_method_with_parameter(self):
        try:
            register(codename='can_ship', field_name='canShip', ModelType=Dummy, view_param_pk='idDummy', description="Only supplier have the authorization to ship")
        except:
            self.fail('')

    def test_method_no_parameters(self):
        try:
            register(codename='can_trash', field_name='canTrash', ModelType=Dummy, view_param_pk='idDummy', description="User can trash a package")
        except:
            self.fail('')

    def test_method_wrong_number_parameters(self):
        self.assertRaises(RulesError, lambda: register(codename='can_trash', field_name='invalidNumberParameters', ModelType=Dummy,
                                                                        view_param_pk='idDummy', description="Rule should not be created, too many parameters"))


class UtilsTest(TestCase):
    def test_register_valid_rules(self):
        try:
            register(codename='can_ship', ModelType=Dummy, field_name='canShip', view_param_pk='idView', description="Only supplier has the authorization to ship")
        except:
            self.fail("test_register_valid_rules failed")

    def test_register_invalid_rules_NonexistentFieldName(self):
        self.assertRaises(NonexistentFieldName, lambda: register(codename='can_ship', ModelType=Dummy, field_name='canSship',
            view_param_pk='idView', description="Only supplier has the authorization to ship"))

    def test_register_valid_rules_compact_style(self):
        try:
            register(codename='canShip', ModelType=Dummy)
        except:
            self.fail("test_register_valid_rules_compact_style failed")

    def test_override_already_registered_rule(self):
        register(codename='canShip', ModelType=Dummy)
        sys.stderr = stderr = StringIO()  # let's capture the warning
        register(codename='canShip', ModelType=Dummy)
        sys.stderr = sys.__stderr__

        self.assertTrue((True if "being overwritten" in stderr.getvalue() else False))
