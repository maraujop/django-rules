# -*- coding: utf-8 -*-
from django.test import TestCase
from django.contrib.auth.models import User, AnonymousUser
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.conf import settings

from django_rules.models import RulePermission
from models import Dummy
from django_rules.exceptions import NonexistentFieldName
from django_rules.exceptions import NotBooleanPermission
from django_rules.exceptions import NonexistentPermission
from django_rules.exceptions import RulesError
from django_rules import utils

class BackendTest(TestCase):
    def setUp(self):
        try:
            self.anonymous = User.objects.get_or_create(id=settings.ANONYMOUS_USER_ID, username='anonymous', is_active=True)[0]
        except Exception:
            self.fail("You need to define an ANONYMOUS_USER_ID in your settings file")
        
        self.user = User.objects.get_or_create(username='javier', is_active=True)[0]
        self.otherUser = User.objects.get_or_create(username='juan', is_active=True)[0]
        self.superuser = User.objects.get_or_create(username='miguel', is_active=True, is_superuser=True)[0]
        self.not_active_superuser = User.objects.get_or_create(username='rebeca', is_active=False, is_superuser=True)[0]
        self.obj = Dummy.objects.get_or_create(supplier=self.user)[0]
        self.ctype = ContentType.objects.get_for_model(self.obj)
        
        self.rule = RulePermission.objects.get_or_create(codename='can_ship', field_name='canShip', content_type=self.ctype, view_param_pk='idDummy',
                                            description="Only supplier have the authorization to ship")[0]

    
    def test_regularuser_has_perm(self):
        self.assertTrue(self.user.has_perm('can_ship', self.obj))
    
    def test_regularuser_has_not_perm(self):
        self.assertFalse(self.otherUser.has_perm('can_ship', self.obj))
    
    def test_regularuser_has_property_perm(self):
        """
        Checks that the backend can work with properties
        """
        RulePermission.objects.get_or_create(codename='can_trash', field_name='isDisposable', content_type=self.ctype, view_param_pk='idDummy',
                                            description="Checks if a user can trash a package")

        try:
            self.user.has_perm('can_trash',self.obj)
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
        self.assertRaises(NonexistentPermission, lambda:self.user.has_perm('nonexistent_perm', self.obj))

    def test_nonboolean_attribute(self):
        RulePermission.objects.get_or_create(codename='wrong_rule', field_name='name', content_type=self.ctype, view_param_pk='idDummy',
                                            description="Wrong rule. The field_name exists so It is created, but it does not return True or False")
        
        self.assertRaises(NotBooleanPermission, lambda:self.user.has_perm('wrong_rule', self.obj))

    def test_nonboolean_method(self):
        RulePermission.objects.get_or_create(codename='wrong_rule', field_name='methodInteger', content_type=self.ctype, view_param_pk='idDummy',
                                            description="Wrong rule. The field_name exists so It is created, but it does not return True or False")
        
        self.assertRaises(NotBooleanPermission, lambda:self.user.has_perm('wrong_rule', self.obj))
    
    def test_nonexistent_field_name(self):
        # Dinamycally removing canShip from class Dummy to test an already existent rule that doesn't have a valid field_name anymore
        fun = Dummy.canShip
        del Dummy.canShip
        self.assertRaises(NonexistentFieldName, lambda:self.user.has_perm('can_ship', self.obj))
        Dummy.canShip = fun

    def test_has_perm_method_no_parameters(self):
        RulePermission.objects.get_or_create(codename='canTrash', field_name='canTrash', content_type=self.ctype, view_param_pk='idDummy',
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
        self.assertRaises(RulesError, lambda:self.user.has_perm('can_ship', self.obj))
        del settings.CENTRAL_AUTHORIZATIONS

    def test_central_authorizations_right_module_nonexistent_function(self):
        settings.CENTRAL_AUTHORIZATIONS = 'utils2'
        self.assertRaises(RulesError, lambda:self.user.has_perm('can_ship', self.obj))
        del settings.CENTRAL_AUTHORIZATIONS

    def test_central_authorizations_right_module_wrong_number_parameters(self):
        settings.CENTRAL_AUTHORIZATIONS = 'utils3'
        self.assertRaises(RulesError, lambda:self.user.has_perm('can_ship', self.obj))
        del settings.CENTRAL_AUTHORIZATIONS


class RulePermissionTest(TestCase):
    def setUp(self):
        self.user = User.objects.get_or_create(username='javier', is_active=True)[0]
        self.obj = Dummy.objects.get_or_create(supplier=self.user)[0]
        self.ctype = ContentType.objects.get_for_model(self.obj)

    def test_invalid_field_name(self):
        self.assertRaises(NonexistentFieldName, lambda:RulePermission.objects.get_or_create(codename='can_ship', field_name='invalidField', content_type=self.ctype, 
                                                                        view_param_pk='idDummy', description="Only supplier have the authorization to ship"))
        
    def test_invalid_field_name(self):
        self.assertRaises(NonexistentFieldName, lambda:RulePermission.objects.get_or_create(codename='can_ship', field_name='invalidField', content_type=self.ctype, 
                                                                        view_param_pk='idDummy', description="Only supplier have the authorization to ship"))
        
    def test_valid_attribute(self):
        self.assertTrue(RulePermission.objects.get_or_create(codename='can_ship', field_name='supplier', content_type=self.ctype, 
                                                                        view_param_pk='idDummy', description="Only supplier have the authorization to ship")[1])

    def test_method_with_parameter(self):
        self.assertTrue(RulePermission.objects.get_or_create(codename='can_ship', field_name='canShip', content_type=self.ctype, 
                                                                        view_param_pk='idDummy', description="Only supplier have the authorization to ship")[1])
    
    def test_method_no_parameters(self):
        self.assertTrue(RulePermission.objects.get_or_create(codename='can_trash', field_name='canTrash', content_type=self.ctype, 
                                                                        view_param_pk='idDummy', description="User can trash a package")[1])

    def test_method_wrong_number_parameters(self):
        self.assertRaises(RulesError, lambda:RulePermission.objects.get_or_create(codename='can_trash', field_name='invalidNumberParameters', content_type=self.ctype, 
                                                                        view_param_pk='idDummy', description="Rule should not be created, too many parameters"))


class UtilsTest(TestCase):
    def test_register_valid_rules(self):
        rules_list = [
            # Dummy model
            {'codename':'can_ship', 'model':'Dummy', 'field_name':'canShip', 'view_param_pk':'idView', 'description':"Only supplier has the authorization to ship"},
        ]

        try:
            for params in rules_list:
                utils.register(app_name="tests", **params)
        except Exception:
            self.fail("test_register_valid_rules failed")

    def test_register_invalid_rules_NonexistentFieldName(self):
        rules_list = [
            # Dummy model
            {'codename':'can_ship', 'model':'Dummy', 'field_name':'canSship', 'view_param_pk':'idView', 'description':"Only supplier has the authorization to ship"},
        ]

        for params in rules_list:
            self.assertRaises(NonexistentFieldName, lambda: utils.register(app_name="tests", **params))

    def test_register_valid_rules_compact_style(self):
        rules_list = [
            # Dummy model
            {'codename':'canShip', 'model':'Dummy'},
        ]

        try:
            for params in rules_list:
                utils.register(app_name="tests", **params)
        except Exception:
            self.fail("test_register_valid_rules_compact_style failed")


