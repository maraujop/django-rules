# -*- coding: utf-8 -*-
from django.shortcuts import get_object_or_404
from django.utils.http import urlquote
from django.conf import settings
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.http import HttpResponseForbidden
from django.http import HttpResponseRedirect
from django.utils.functional import wraps
from django.shortcuts import get_object_or_404
from django.core.urlresolvers import NoReverseMatch, reverse

from exceptions import RulesError
from exceptions import NonexistentPermission
from models import RulePermission
from backends import ObjectPermissionBackend


def object_permission_required(perm, **kwargs):
    """
    Decorator for views that checks whether a user has a particular permission

    The view needs to have a parameter name that matches rule's view_param_pk.
    The value of this parameter will be taken as the primary key of the model.

    :param login_url: if denied, user would be redirected to location set by
      this parameter. Defaults to ``django.conf.settings.LOGIN_URL``.
    :param redirect_field_name: name of the parameter passed if redirected.
      Defaults to ``django.contrib.auth.REDIRECT_FIELD_NAME``.
    :param return_403: if set to ``True`` then instead of redirecting to the
      login page, response with status code 403 is returned (
      ``django.http.HttpResponseForbidden`` instance). Defaults to ``False``.

    Examples::

        # RulePermission.objects.get_or_create(codename='can_ship',...,view_param_pk='paramView')
        @permission_required('can_ship', return_403=True)
        def my_view(request, paramView):
            return HttpResponse('Hello')

    """

    login_url = kwargs.pop('login_url', settings.LOGIN_URL)
    redirect_url = kwargs.pop('redirect_url', "")
    redirect_field_name = kwargs.pop('redirect_field_name', REDIRECT_FIELD_NAME)
    return_403 = kwargs.pop('return_403', False)

    # Check if perm is given as string in order to not decorate
    # view function itself which makes debugging harder
    if not isinstance(perm, basestring):
        raise RulesError("First argument, permission, must be a string")

    def decorator(view_func):
        def _wrapped_view(request, *args, **kwargs):
            obj = None
            
            try:
                rule = RulePermission.objects.get(codename = perm)
            except RulePermission.DoesNotExist:
                raise NonexistentPermission("Permission %s does not exist" % perm)

            # Only look in kwargs, if the views are entry points through urls Django passes parameters as kwargs
            # We could look in args using  inspect.getcallargs in Python 2.7 or a custom function that 
            # imitates it, but if the view is internal, I think it's better to force the user to pass 
            # parameters as kwargs
            if rule.view_param_pk not in kwargs: 
                raise RulesError("The view does not have a parameter called %s in kwargs" % rule.view_param_pk)
                
            model_class = rule.content_type.model_class()
            obj = get_object_or_404(model_class, pk=kwargs[rule.view_param_pk])

            if not request.user.has_perm(perm, obj):
                if return_403:
                    return HttpResponseForbidden()
                else:
                    if redirect_url:
                        try:
                            path = urlquote(request.get_full_path())
                            redirect_url_reversed = reverse(redirect_url)
                            tup = redirect_url_reversed, redirect_field_name, path
                        except NoReverseMatch:
                            tup = redirect_url, redirect_field_name, path
                    else:
                        path = urlquote(request.get_full_path())
                        tup = login_url, redirect_field_name, path

                    return HttpResponseRedirect("%s?%s=%s" % tup)
            return view_func(request, *args, **kwargs)
        return wraps(view_func)(_wrapped_view)
    return decorator
