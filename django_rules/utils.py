# -*- coding: utf-8 -*-


import sys

from django.contrib.contenttypes.models import ContentType

from models import RulePermission


def register(app_name, codename, model, field_name='', view_param_pk='', description=''):
    """
    Call this function in your rules.py to register your RulePermissions
    All registered rules will be synced when sync_rules command is run
    """
    if not isinstance(model, (list, tuple)):
        model = [model]

    for m in model:
        # We get the `ContentType` for that model `m` within that `app_name`
        try:
            ctype = ContentType.objects.get(app_label=app_name, model=m.lower())
        except ContentType.DoesNotExist:
            sys.stderr.write("! Rule codenamed %s will not be synced as model %s was not found for app %s\n" % (codename, m, app_name))
            return

        try:
            # We see if the rule"s pk exists, if it does then delete and overwrite it
            rule = RulePermission.objects.get(codename=codename, content_type=ctype)
            rule.delete()
            sys.stderr.write("Careful rule (%s, %s) being overwritten. Make sure its (codename, model) is not repeated in other rules.py files\n" % (codename, m))
            RulePermission.objects.create(codename=codename, content_type=ctype,
                field_name=field_name, view_param_pk=view_param_pk, description=description)

        except RulePermission.DoesNotExist:
            RulePermission.objects.create(codename=codename, content_type=ctype,
                field_name=field_name, view_param_pk=view_param_pk, description=description)
