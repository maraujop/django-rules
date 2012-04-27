#-*- coding: utf-8 -*-
import os
import sys

from django.test.testcases import TestCase

from django.template import Template, Context, TemplateSyntaxError
from django_rules.mem_store import register

from django.contrib.auth.models import User, AnonymousUser

from models import Dummy

import django_rules.templatetags


class TemplatetagsTest(TestCase):
    def setUp(self):
        self.user = User.objects.get_or_create(username='user', is_active=True)[0]
        self.anon = AnonymousUser()
        self.anon.username = 'anonymous'

        self.obj = Dummy.objects.get_or_create(supplier=self.user, name='dummy')[0]

        rule = {
            'codename': 'can_ship',
            'field_name': 'canShip',
            'ModelType': Dummy,
            'view_param_pk': 'idDummy',
            'description': "Only supplier have the authorization to ship",
        }

        sys.stderr = open(os.devnull, 'w')  # silencing the "overwriting" warning
        register(**rule)
        sys.stderr = sys.__stderr__

    def tag_has_perm(self, obj, codename, user=None, varname=None):
        _user = '' if user is None else user.username
        _obj = obj.__class__.__name__
        _as = '' if varname is None or varname is codename else " as %s" % varname
        return "{%% has_perm %s %s.%s %s %%}" % (_user, _obj, codename, _as)

    def has_perm(self, obj, codename, user=None, varname=None, tag=None):
        user = self.user if user is None else user
        varname = "%s_%s" % (obj.__class__.__name__, codename) if varname is None else varname
        tag = self.tag_has_perm(obj, codename, user, varname) if tag is None else tag
        context = {
            obj.__class__.__name__: obj,
            user.username: user,
        }
        template = """
            {% load django_rules %}
            """ + tag + """
            {% if """ + varname + """ %}True{% else %}{% endif %}
            """
        return bool(Template(template).render(Context(context)).strip())

    def test_valid_tag_syntax(self):
        argz = (
                {'user': None, 'varname': None},
                {'user': self.user, 'varname': None},
                {'user': None, 'varname': 'varname'},
                {'user': self.user, 'varname': 'varname'},
        )

        for arg in argz:
            arg['tag'] = self.tag_has_perm(self.obj, 'can_ship', arg['user'], arg['varname'])
            has_perm = self.has_perm(self.obj, 'can_ship', **arg)
            self.assertTrue(has_perm)

    def test_invalid_tag_syntax(self):
        template_tags = (
            "{% has_perm      USER     OBJ.PERM  BOGUS %}",
            "{% has_perm      USER     OBJ.PERM  xx       BOOLEANVAR %}",
        )

        for tag in template_tags:
            self.assertRaisesRegexp(TemplateSyntaxError, "Incorrect 'has_perm' template tag syntax",
                    self.has_perm, self.obj, 'can_ship', None, **{'tag': tag})

    def test_active_owner_for_permission(self):
        self.assertTrue(self.has_perm(self.obj, 'can_ship'))

    def test_anonymous_user_for_permission(self):
        self.assertFalse(self.has_perm(self.obj, 'can_ship', self.anon))

    def test_other_user_for_permission(self):
        self.assertFalse(self.has_perm(self.obj, 'can_ship', User(username='otherUser')))

    def test_inactive_user_for_permission(self):
        self.assertFalse(self.has_perm(self.obj, 'can_ship', User(username='inactive', is_active=False)))

    def test_active_owner_against_missing_permission(self):
        self.assertFalse(self.has_perm(self.obj, 'other_perm'))
