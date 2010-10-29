# -*- coding: utf-8 -*-
import inspect
from django.core.exceptions import ValidationError
from django.db import models
from django.contrib.contenttypes.models import ContentType

from exceptions import NonexistentFieldName
from exceptions import RulesError


class RulePermission(models.Model):
    """
    This model holds the rules for the authorization system
    """
    codename = models.CharField(primary_key=True, max_length=30)
    field_name = models.CharField(max_length=30)
    content_type = models.ForeignKey(ContentType)
    view_param_pk = models.CharField(max_length=30)
    description = models.CharField(max_length=140, null=True)


    def save(self, *args, **kwargs):
        """
        Validates that the field_name exists in the content_type model
        raises ValidationError if it doesn't. We need to restrict security rules creation
        """
        # If not set use codename as field_name as default
        if self.field_name == '':
            self.field_name = self.codename

        # If not set use primary key attribute name as default
        if self.view_param_pk == '':
            self.view_param_pk = self.content_type.model_class()._meta.pk.get_attname()

        # First search for a method or property defined in the model class
        # Then we look in the meta field_names
        # If field_name does not exist a ValidationError is raised
        if not hasattr(self.content_type.model_class(), self.field_name):
            # Search within attributes field names
            if not (self.field_name in self.content_type.model_class()._meta.get_all_field_names()):
                raise NonexistentFieldName("Could not create rule: field_name %s of rule %s does not exist in model %s" %
                                            (self.field_name, self.codename, self.content_type.model))
        else:
            # Check if the method parameters are less than 2 including self in the count
            bound_field = getattr(self.content_type.model_class(), self.field_name)
            if callable(bound_field):
                if len(inspect.getargspec(bound_field)[0]) > 2:
                    raise RulesError("method %s from rule %s in model %s has too many parameters." %
                                        (self.field_name, self.codename, self.content_type.model))
        
        super(RulePermission, self).save(*args, **kwargs)
