# -*- coding: utf-8 -*-
from django.db import models
from django.contrib.auth.models import User

class Dummy(models.Model):
    """
    Dummy model for testing permissions
    """
    idDummy = models.AutoField(primary_key = True)
    supplier = models.ForeignKey(User, null = False)
    name = models.CharField(max_length = 20, null = True)

    def canShip(self,user_obj):
        """
        Only the supplier can_ship in our business logic.
        Checks if the user_obj passed is the supplier.
        """
        return self.supplier == user_obj

    @property
    def isDisposable(self):
        """
        It should check some attributes to see if 
        package is disposable
        """
        return True

    def canTrash(self):
        """
        Methods can either have a user_obj parameter
        or no parameters
        """
        return True

    def methodInteger(self):
        """
        This method does not return a boolean value
        """
        return 2

    def invalidNumberParameters(self, param1, param2):
        """
        This method has too many parameters for being a rule
        """
        pass
        

