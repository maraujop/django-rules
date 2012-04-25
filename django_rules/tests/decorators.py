# -*- coding: utf-8 -*-


from django.test import TestCase
from django.contrib.auth.models import User, AnonymousUser
from django.http import HttpRequest, HttpResponse, Http404, HttpResponseRedirect

from django_rules.exceptions import RulesError, NonexistentPermission
from django_rules.decorators import object_permission_required
from django_rules.mem_store import register
from .models import Dummy



class DecoratorsTest(TestCase):
    def setUp(self):
        # Users
        self.user = User.objects.get_or_create(username='javier', is_active=True)[0]
        self.otheruser = User.objects.get_or_create(username='miguel', is_active=True)[0]

        # Dummy object for checking rules
        self.obj = Dummy.objects.get_or_create(idDummy=1,supplier=self.user)[0]

        register(codename='can_ship', field_name='canShip', ModelType=Dummy, view_param_pk='idView', description="Only supplier have the authorization to ship")
        register(codename='can_supply', field_name='canShip', ModelType=Dummy, view_param_pk='nonexistent_param',
                                                            description="view_param_pk does not match idView param from dummy_view")

    def _get_request(self, user=None):
        if user is None:
            user = AnonymousUser()
        request = HttpRequest()
        request.user = user
        return request

    def _dummy_view(self, user_obj, dicc, value):
        @object_permission_required(**dicc)
        def dummy_view(request, idView):
            return HttpResponse('success')

        request = self._get_request(user_obj)
        return dummy_view(request, idView=value)

    def test_wrong_args(self):
        self.assertRaises(RulesError, lambda: self._dummy_view(self.user, {'ModelType': Dummy, 'codename': 2}, self.obj.pk))

    def test_with_permission(self):
        response = self._dummy_view(self.user, {'ModelType': Dummy, 'codename': 'can_ship'}, self.obj.pk)
        self.assertEqual(response.content, 'success')

    def test_without_permission_403(self):
        response = self._dummy_view(self.otheruser, {'ModelType': Dummy, 'codename': 'can_ship', 'return_403': True}, self.obj.pk)
        self.assertEqual(response.status_code, 403)

    def test_nonexistent_permission(self):
        self.assertRaises(NonexistentPermission, lambda: self._dummy_view(self.user, {'ModelType': Dummy, 'codename': 'nonexistent_perm'}, self.obj.pk))

    def test_nonexistent_obj(self):
        last=int(Dummy.objects.latest(field_name='pk').pk)
        self.assertRaises(Http404, lambda: self._dummy_view(self.user, {'ModelType': Dummy, 'codename': 'can_ship'}, last+1))

    def test_without_permission_redirection(self):
        response = self._dummy_view(self.otheruser, {'ModelType': Dummy, 'codename': 'can_ship', 'login_url': '/foobar/'}, self.obj.pk)
        self.assertTrue(isinstance(response, HttpResponseRedirect))
        self.assertTrue(response._headers['location'][1].startswith('/foobar/'))

    def test_view_param_pk_not_match_param_in_view(self):
        self.assertRaises(RulesError, lambda: self._dummy_view(self.user, {'ModelType': Dummy, 'codename': 'can_supply'}, self.obj.pk))

    def test_redirect_url_reverse_match(self):
        response = self._dummy_view(self.otheruser, {'ModelType': Dummy, 'codename': 'can_ship', 'redirect_url': 'home'}, self.obj.pk)
        self.assertTrue(isinstance(response, HttpResponseRedirect))
        self.assertTrue(response._headers['location'][1].startswith('/'))

    def test_redirect_url_no_reverse_match(self):
        response = self._dummy_view(self.otheruser, {'ModelType': Dummy, 'codename': 'can_ship', 'redirect_url': '/foo/bar/'}, self.obj.pk)
        self.assertTrue(isinstance(response, HttpResponseRedirect))
        self.assertTrue(response._headers['location'][1].startswith('/foo/bar/'))
