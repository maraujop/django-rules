# -*- coding: utf-8 -*-
from collections import defaultdict
import inspect
import sys

from django.db.models.fields import FieldDoesNotExist

from exceptions import NonexistentFieldName
from exceptions import RulesError


_mem_store = defaultdict(dict)

def get(perm, model):
    return _mem_store.get(model, {}).get(perm, None)


class RulePermission(object):
    """
    This model holds the rules for the authorization system
    """
    def __init__(self, codename, ModelType, field_name=None, view_param_pk=None, description=''):
        """
        :param codename: The name of the rule
        :param ModelType: The model class
        :param field_name: The name of the model method to call to for checking the rule's constraint
        :param view_param_pk: The view's parameter's name to use for getting the primary key of the model. Used in decorated views.
        :param description: A brief description explaining the expected behavior of the rule.
        """
        self.codename = codename
        self.ModelType = ModelType
        self.field_name = field_name
        self.view_param_pk = view_param_pk
        self.description = description


def register(codename, ModelType, field_name=None, view_param_pk=None, description=''):
    """
    TODO: Add doc
    """
    # Defaults
    field_name = field_name if field_name is not None else codename
    view_param_pk = view_param_pk if view_param_pk is not None else ModelType._meta.pk.attname

    # we check if field_name is a property or method of the model
    if not hasattr(ModelType, field_name):
        try:
            # Check if field_name is a field of the model, not a property or function
            ModelType._meta.get_field_by_name(field_name)
        except FieldDoesNotExist:
            raise NonexistentFieldName("Could not create rule: field_name %s of rule %s does not exist in model %s" %
                                    (field_name, codename, str(ModelType)))

    # If field_name is a method, check if the method parameters are less than 2 including self in the count
    bound_field = getattr(ModelType, field_name, False)
    
    if not bound_field:
        try:
            ModelType._meta.get_field_by_name(field_name)[0]
        except ModelType.DoesNotExist:
            raise NonexistentFieldName("Could not create rule: field_name %s of rule %s does not exist in model %s" %
                                    (field_name, codename, str(ModelType)))

    if callable(bound_field):
        if len(inspect.getargspec(bound_field)[0]) > 2:
            raise RulesError("method %s from rule %s in model %s has too many parameters." % (
                field_name, 
                codename, 
                str(ModelType)
            ))

    # We see if the rule's codename exists, if it does warn overwriting
    if codename in _mem_store[ModelType].keys():
        sys.stderr.write("Careful rule %s being overwritten, make sure it has not been registered twice\n" % codename)

    _mem_store[ModelType].update({
        codename: RulePermission(
            codename, 
            ModelType, 
            field_name, 
            view_param_pk, 
            description
        )
    })
