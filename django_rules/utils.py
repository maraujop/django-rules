# -*- coding: utf-8 -*-
from models import RulePermission
from django.contrib.contenttypes.models import ContentType
    
def register(app_name, codename, model, field_name='', view_param_pk='', description=''):
    """
    Call this function in your rules.py to register your RulePermissions
    All registered rules will be synced when sync_rules command is run
    """
    # We get the `ContentType` for that `model` within that `app_name`
    try:
        ctype = ContentType.objects.get(app_label = app_name, model = model)
    except ContentType.DoesNotExist:
        print "! Rule codenamed %s will not be synced as model %s was not found for app %s" % (codename, model, app_name)
        return

    try:
        # We see if the rule's pk exists, if it does then delete and overwrite it
        rule = RulePermission.objects.get(pk = codename)
        rule.delete()
        print "Careful rule %s being overwritten. Make sure its codename is not repeated in two rules.py files" % codename
        RulePermission.objects.create(codename=codename, field_name=field_name, content_type=ctype,
                    view_param_pk=view_param_pk, description=description)

    except RulePermission.DoesNotExist:
        RulePermission.objects.create(codename=codename, field_name=field_name, content_type=ctype,
                    view_param_pk=view_param_pk, description=description)
