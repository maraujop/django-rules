# -*- coding: utf-8 -*-
from django.test import TestCase
from django.contrib.auth.models import User, AnonymousUser
from django.contrib.contenttypes.models import ContentType
from django.http import HttpRequest, HttpResponse, Http404, HttpResponseRedirect

from django_rules.exceptions import RulesError, NonexistentPermission
from django_rules.models import RulePermission
from django_rules.decorators import object_permission_required
from models import Dummy

class DecoratorsTest(TestCase):
    def setUp(self):
        self.user = User.objects.get_or_create(username='javier', is_active=True)[0]
        self.otheruser = User.objects.get_or_create(username='miguel', is_active=True)[0]
        self.obj = Dummy.objects.get_or_create(idDummy=1,supplier=self.user)[0]
        self.ctype = ContentType.objects.get_for_model(self.obj)
        self.rule = RulePermission.objects.get_or_create(codename='can_ship', field_name='canShip', content_type=self.ctype, view_param_pk='idView',
                                                            description="Only supplier have the authorization to ship")
        self.wrong_pk_rule = RulePermission.objects.get_or_create(codename='can_supply', field_name='canShip', content_type=self.ctype, view_param_pk='nonexistent_param',
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


    def test_no_args(self):
        try:
            @object_permission_required
            def dummy_view(request):
                return HttpResponse('dummy_view')
        except RulesError:
            pass
        else:
            self.fail("Trying to decorate using permission_required without permission as first argument should raise exception")

    def test_wrong_args(self):
        self.assertRaises(RulesError, lambda:self._dummy_view(self.user,{'perm':2},self.obj.pk))

    def test_with_permission(self):
        response = self._dummy_view(self.user, {'perm':'can_ship'}, self.obj.pk)
        self.assertEqual(response.content, 'success')

    def test_without_permission_403(self):
        response = self._dummy_view(self.otheruser, {'perm':'can_ship','return_403':True}, self.obj.pk)
        self.assertEqual(response.status_code, 403)

    def test_nonexistent_permission(self):
        self.assertRaises(NonexistentPermission, lambda: self._dummy_view(self.user, {'perm':'nonexistent_perm'}, self.obj.pk))

    def test_nonexistent_obj(self):
        last=int(Dummy.objects.latest(field_name='pk').pk)
        self.assertRaises(Http404, lambda: self._dummy_view(self.user, {'perm':'can_ship'}, last+1))

    def test_without_permission_redirection(self):
        response = self._dummy_view(self.otheruser, {'perm':'can_ship','login_url':'/foobar/'}, self.obj.pk)
        self.assertTrue(isinstance(response, HttpResponseRedirect))
        self.assertTrue(response._headers['location'][1].startswith('/foobar/'))

    def test_view_param_pk_not_match_param_in_view(self):
        self.assertRaises(RulesError, lambda: self._dummy_view(self.user, {'perm':'can_supply'}, self.obj.pk))
        

