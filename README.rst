############
django-rules
############

django-rules is a Django authorization backend that offers a unified, per-object
authorization management. It is quite different from other authorization
backends in the way it lets you flexibly manage per-object permissions.

In django-rules every rule adds an authorization constraint to a given model.
The authorization constraint will check if the given user complies with the
constraint (e.g. if the user has the right permissions to execute a certain
action over an object, etc.). The authorization constraint can be a boolean
attribute, property or method of the model, whichever you prefer for each rule
:)


Philosophy
==========

django-rules strives to build a flexible and scalable authorization backend. Why
is it better than other authorization backends out there?

* The backend is simple, concise and compact. Less lines of code mean less
  complexity, faster execution and (hopefully :) less errors and bugs.
* You can implement each authorization constraint as a boolean attribute,
  property or method of the model, whichever you prefer for each rule. This way
  you will be able to re-implement how authorizations work at any time. It is
  dynamic and you know dynamic sounds way better than static :)
* You don't have to add extra permissions or groups to your users. You simply
  program the constraints however you like them to be and then you assign them
  to the rules. Done!
* You have fine granularity control over how the rules handle the
  authentication: one rule can be using an authorization constraint that uses
  LDAP while other rules call a web service (or anything you wish to hook in the
  authorization constraint).
* Other per-object authorization backends create a row in a table for every
  combination of object, user and permission. Even with an average-size site,
  you will have scalability nightmares, no matter how much you cache.
* Other authorization backends have to SELECT all permissions that a user has
  even if you only need to check one specific permission, making the memory
  footprint bigger.
* Other authorization backends don't have a way to set centralized permissions,
  which are a real necessity in most projects out there.


Requirements
============

django-rules requires a proper installation of Django 1.2 (at least).


Installation
============

From Pypi
---------

As simple as doing::

    pip install django-rules

From source
-----------

To install django-rules from source::

    git clone https://github.com/maraujop/django-rules/
    cd django-rules
    python setup.py install


Configuration
=============

For django-rules to work, you have to hook it into your project:

* Add it to the list of ``INSTALLED_APPS`` in ``settings.py``::

    INSTALLED_APPS = (
        ...
        'django_rules',
    )

* Add the django-rules authorization backend to the list of
  ``AUTHENTICATION_BACKENDS`` in ``settings.py`` (mind the order!)::

    AUTHENTICATION_BACKENDS = (
        'django.contrib.auth.backends.ModelBackend', # Django's default auth backend
        'django_rules.backends.ObjectPermissionBackend',
    )

* Run syncdb to update the database with the new django-rules models::

    python manage.py syncdb


Rules
=====

A rule represents a functional authorization constraint that restricts the
actions that a certain user can carry out on a certain object (an instance of a
Model).

Every rule definition is composed of 6 parameters (3 compulsory and 3 optional):

* ``app_name``: The name of the app to which the rule applies.
* ``codename``: The name of the rule. It should be a brief but distinctive name.
* ``model``: The name of the model or the list of names of the models associated
  with the rule.

Note that the (``codename``, ``model``) tuple (or the tuples in case ``model`` is a
list of model names) will be unique.

* ``field_name`` *(optional)*: The name of the boolean attribute, property or
  method of the model that implements the authorization constraint. If not set,
  it defaults to the ``codename`` (that is, it will look for a field named exactly
  like the rule).
* ``view_param_pk`` *(optional)*: The view parameter's name to use for getting the
  primary key of the model. It is used in the decorated views for getting the
  actual instance of the model, that is, the object against which the
  authorizations will be checked. If not set, it defaults to the name of the
  primary key field in the model. Note that if the name of the parameter of the
  view that holds the value of the object's primary key doesn't match the name
  of the primary key of the model, the new name must be specified in this
  parameter (we will talk about this special case in the section on
  _`Decorators`).
* ``description`` *(optional)*: A brief (140 characters maximum) description
  explaining the expected behaviour of the authorization constraint. Although
  optional, it is considered a Good Practice™ and should always be used.

The rules should be created per-Django application. That is, under the root
directory of the Django-application in which you want to create rules, you
should have a ``rules.py`` containing only the declarations of those rules
specific to that Django-application.

Once you have defined the rules in ``rules.py``, you will want to activate them.
For every rule that you want to activate you **must** add a registration point
for it by calling ``django_rules.utils.register`` in ``rules.py``.

Finally, once you have ``rules.py`` properly set up, you will want to sync the
rules to the database. In your Django project you will have to run ``sync_rules``
command::

    python manage.py sync_rules

This command will look for all your ``rules.py`` files under your ``INSTALLED_APPS``
and will sync the latest changes to the database, so you don't have to run
``syncdb`` or rebuild the full database at all.


Examples
========

Example 1: Creating a simple, compact rule for the Item model in the 'shipping' Django-application
--------------------------------------------------------------------------------------------------

Let's image that, within the ``shipping`` Django-application, I have the following
``models.py``::

    from django.db import models
    from django.contrib.auth.models import User

    class Item(models.Model):
        supplier = models.ForeignKey(User)
        description = models.CharField(max_length=50)

Then, imagine that the business logic in our application has a functional
authorization constraint for every item such as "An item can only be shipped by
its supplier". Now, to comply with the functional authorization constraint we
only have to create a simple rule.

First, let's start by adding an authorization constraint to the Item model.
Remember that we can use a method, a boolean attribute or a boolean-returning
property. This time we will be using a method::

    from django.db import models
    from django.contrib.auth.models import User

    class Item(models.Model):
        supplier = models.ForeignKey(User)
        description = models.CharField(max_length=50)

        def can_ship(self, user):
            """
            Checks if the given user is the supplier of the item
            """
            return user == self.supplier

Then, to associate the authorization constraint with a rule, we have to set up
the rule in the application's ``rules.py`` file::

    from django_rules import utils

    rules_list = [
        {'codename': 'can_ship', 'model': 'Item'},
    ]
    # NOTE:
    # Although the above rule definition follows the minimal style, it is
    # Good Practice™ to always add the optional 'description' field
    # to give a brief explanation about the expected behaviour of the rule.


    # For the rules to be active, we **must** register them:
    for rule in rules_list:
        utils.register(app_name='shipping', ****rule)

Finally, do not forget to sync the rules to make sure that all the new
definitions, changes, etc. are synced to the database::

    python manage.py sync_rules

Example 2: Sharing the ``codename`` of a rule in multiple models
--------------------------------------------------------------

Imagine we want two (or more) models to have a rule with the same ``codename`` and
we want to be able to conveniently write the rule in the application's
``rules.py`` file.

For example, let's image that we extend _`Example 1` with another model that
also implements a ``can_ship`` rule::

    from django.db import models
    from django.contrib.auth.models import User

    class Item(models.Model):
        supplier = models.ForeignKey(User)
        description = models.CharField(max_length=50)

        def can_ship(self, user):
            """
            Checks if the given user is the supplier of the item
            """
            return user == self.supplier

    class Postcard(models.Model):
        supplier = models.ForeignKey(User)
        description = models.CharField(max_length=50)

        def can_ship(self, user):
            """
            Everybody can send a postcard :)
            """
            return True

Then, the ``rules_list`` in the application's ``rules.py`` file will look like::

    rules_list = [
        {'codename': 'can_ship', 'model': 'Item'},
        {'codename': 'can_ship', 'model': 'Postcard'},
    ]

or, condensed in one line::

    rules_list = [
        {'codename': 'can_ship', 'model': ['Item', 'Postcard']},
    ]

Example 3: Creating a rule that doesn't follow the naming conventions
---------------------------------------------------------------------

Imagine that we would like to name our authorization constraints however we
want. For example, let's change the previous Item model::

    from django.db import models
    from django.contrib.auth.models import User

    class Item(models.Model):
        supplier = models.ForeignKey(User)
        description = models.CharField(max_length=50)

        def is_same_supplier(self, user):    #--> change in the name convention of the authorization constraint
            """
            Checks if the given user is the supplier of the item
            """
            return user == self.supplier

Then, we would have to set up a more verbose rule in the application's
``rules.py`` file by using its additional optional fields. This time, only
``field_name`` would be needed but it is also Good Practice™ to give a brief
``description``::

    from django_rules import utils

    rules_list = [
        {
            'description': 'Checks if the given user is the supplier of the item',
            'codename': 'can_ship', 'model': 'Item', 'field_name': 'is_same_supplier',
        },
    ]

    # For the rules to be active, we **must** register them:
    for rule in rules_list:
        utils.register(app_name='shipping', ****rule)

Again, do not forget to sync the rules to make sure that all the new
definitions, changes, etc. are applied to the database::

    python manage.py sync_rules

Using your rules
----------------

Once you have set up a rule that implements a functional authorization
constraint, you can (and should :) use it in your application. It is really
simple! In every place you want to enforce an authorization constraint on a
user, you will simply make the following call::

    user.has_perm(codename, obj)

Following the previous _`Example 1`, let's imagine that the application is
already running with data in the database (at least one supplier and one item,
both with ids equal to 1). Remember that we have already implemented, defined,
registered and synced the following rule::

    {'codename': 'can_ship', 'model': 'Item'}

Then, if we wanted to check whether a supplier can ship an item, we would only
have to enforce the rule by doing::

    supplier = Supplier.objects.get(pk=1)
    item = Item.objects.get(pk=1)

    if supplier.has_perm('can_ship', item):
        print 'Yay! The supplier can ship the item! :)'

Easy, right? :)

Details about the internal magic of django-rules
................................................

Please note that what follows is a detailed explanation of how all the inner
magic in django-rules flows. If you don't really care, please move along. You
really don't need these details to be able to write rules and use django-rules
effectively. However, if you are curious and want to know more, please pay great
attention to the details below.

Here is how all the pieces of the puzzle come together:

* When you call ``user.has_perm(codename, obj)`` (in the previous
  example, ``supplier.has_perm('can_ship', item)``), Django handles the control
  over to the django-rules backend.
* The django-rules backend will then try to match the ``codename`` with a rule.
  Note that we are requesting a rule with a ``codename`` of ``'can_ship'`` and a
  ``obj`` like the Model of the item object. Because in _`Example 1` we
  have defined the rule ``{'codename': 'can_ship', 'model': 'Item'}``, there
  will be a match.
* Then, django-rules will check whether ``field_name`` is an attribute, a
  property or a method, and will act accordingly. If ``field_name`` is a method,
  the django-rules backend will check if it requires just one user parameter or
  no parameter at all. Depending on the parameter requirements, it will execute
  ``obj.field_name()`` or ``obj.field_name(user)``. In our
  _`Example 1` we require a user parameter so it will execute
  ``item.can_ship(supplier)``.
* Finally, if the authorization constraint implemented in ``field_name`` is
  ``True`` or returns ``True``, the constraint is considered fulfilled.
  Otherwise, you will not be authorized.

Details of using model methods in rules
---------------------------------------

As we have seen, django-rules will check whether ``field_name`` is an attribute, a
property or a method, and will act accordingly. That is, for the very simple
cases, you can create rules based on the attributes and properties of a model.
But in real life applications most of the time you will probably be setting
``field_name`` to a method in the model.

It is important to note that this method is limited to having just one parameter
(a user object) or no parameters at all. It cannot receive multiple arguments or
an argument that is not an instance of User. Although this might seem like a
limitation, we could not think of a use case where the rest of the information
needed coudn't be retrieved from the user or the model object. If you get into a
situation where this is limiting you, please get in touch and explain your
problem so that we can think of how to get around it! :)

Finally, you need to be aware of something very important: a method assigned to
a rule (let's call them *rule methods* from now on) **should never call any
other method**. That is, they should be self-contained. This is to avoid a
potential infinite recursion. Imagine a situation where the rule method calls
another method that has *the same* authorization constraint of the previous rule
method. Boom! You just created an infinite loop. Run for your life! :)

You may be thinking that you can control this but, trust me, it will get very
difficult to maintain and scale. Things will not always be that simple, maybe
you will end up calling a method that is later modified and ends up calling a
helper function that triggers the same authorization loop. Yeah, I know.
Indirection is a bitch :) Or, in other words "Great power comes with great
responsibility". So beware of the infinite loop ;)


Decorators
==========

If you like Python as much as I do, you will love decorators. Django has a
``permission_required`` decorator, so it felt natural that django-rules
implemented an ``object_permission_required`` decorator.

Imagine that for our _`Example 1` we have the following code in ``views.py``::

    def ship_item(request, id):
        item = Item.objects.get(pk = id)

        if request.user.has_perms('can_ship', item):
            return HttpResponse('success')

        return HttpResponse('error')

We could easily decorate the view to make the method much more compact and easy
to read::

    from django_rules import object_permission_required

    @object_permission_required('can_ship')
    def ship_item(request, id):
        return HttpResponse('Item successfully shipper! :)')

The magic of the decorator is very cool indeed. First, it matches the rule and
gets the type of model from it. Then, it gets the ``id`` parameter from the view's
kwargs and instantiates a Model object with ``item = model.objects.get(pk = id)``.
Finally, it can call the ``request.user.has_perm('can_ship', item)`` for you and
redirect to a fail page if the constraint is not fulfilled.

Note how we have maintained the name of the model's primary key in the
parameters of the view. If the parameter has a name that doesn't match the name
of the primary key in the model, remember that we will have to add another
optional parameter to the rule. From the section on _`Rules`:

* ``view_param_pk`` *(optional)*: The view parameter's name to use for getting the
  primary key of the model. It is used in the decorated views for getting the
  actual instance of the model. If not set, it defaults to the name of the
  primary key field in the model. Note that if the name of the parameter of the
  view that holds the value of the object's primary key doesn't match the name
  of the primary key of the model, the new name must be specified in this
  parameter.

For example, if we modify the parameter of the view::

    from django_rules import object_permission_required

    @object_permission_required('can_ship')
    def ship_item(request, my_item_code):  #--> change in the naming of the parameter in the view
        return HttpResponse('success')

We would have to specify the ``view_param_pk`` in the rule definition::

    rules_list = [
        {'codename': 'can_ship', 'model': 'Item', 'view_param_pk': 'my_item_code',
         'description': 'Checks if the given user is the supplier of the item'},
    ]


The ``object_permission_required`` decorator can receive 4 arguments::

    @object_permission_required('can_ship', return_403=True)
    @object_permission_required('can_ship', redirect_url='/more/foo/bar/')
    @object_permission_required('can_ship', redirect_field_name='myFooField')
    @object_permission_required('can_ship', login_url='/foo/bar/')

By default:

* ``return_403`` is set to False.
* ``redirect_url`` is set to an empty string.
* ``redirect_field_name`` is set to ``django.contrib.auth.REDIRECT_FIELD_NAME``.
* ``login_url`` is set to ``settings.LOGIN_URL``.

Thus, if the authorization constraint is not fulfilled, the decorator will
default to a redirect to the login page in Django-style :)

Also, note that a couple of the parameters have a specificity. Namely:

* if ``return_403`` is set to ``True`` it will override the rest of the
  parameters and the decorator will return a ``HttpResponseForbidden``.
* if ``redirect_url`` is set to a URL, it will override that of ``login_url``.

Finally, it is important to note a tricky detail regarding the use of the
decorator to guard the access of those methods that are not directly exposed as
views mapped to external URLs. When a view method is an entry point through URLs
(that is, if your view method is mapped directly to one of the ``urls.py``
entries), Django parses the URL and passes the parameters to the view as
``kwargs``. Thus, if you want to use the ``object_permission_required`` decorator
over an internal method (a method that is called inside one of those external
views or somewhere else in your code) you must use ``kwargs`` when passing the
parameters.

Let's see an example::

    def item_shipper(request, id):
        internal_code = 'XXX-' + my_item_code
        return _ship_item(request, id=internal_code)    # instead of doing return _ship_item(request, internal_code)

    @object_permission_required('can_ship')
    def _ship_item(request, id)
        return HttpResponse('success')


Centralized Permissions
=======================

django-rules has a central authorization dispatcher that is aimed towards a very
common need in real life projects: the special, privileged groups such as
administrators, user-support staff, etc., that have permissions to override
certain aspects of the authorization constraints in the application. For such
cases, django-rules has a way to let you bypass its authorization system for
whatever reasons you have.

To set up centralized permissions, you will need to set in your project settings
the variable ``CENTRAL_AUTHORIZATIONS`` pointing to a module. Within that module,
you will have to define a a boolean-returning function named
``central_authorizations`` accepting exactly two parameters:

* ``user``: the user object.
* ``codename``: the codename of the rule we will be overriding. It is very
  useful to refine the permissions of a special user "a la ACL".

Note that, although the naming of the parameters doesn't really matter, the
order does. The first parameter will receive a user object, and the second
parameter, the codename of the rule.

This ``central_authorizations()`` function will be called **before** any other
rule, so you can override all of them here.

For example, in ``settings.py`` you will add::

    CENTRAL_AUTHORIZATIONS = 'myProjectFoo.utils'

And then, within myProjectFoo, in ``utils.py``, you will implement the
``central_authorizations()`` function with the overrides for the special users.

Imagine you want to give some special access to user support staff that will be
able to access some private fields in the profile (for example, email and age)
that generally are hidden to regular users of the application. They are user
support, so they should not be able to override certain things in the
application. Yet, you also want your über-admins (generally the developers) to
be able to access anything within the application so that they can code and test
quickly while developing.

In such case, you can write the following ``central_authorizations()`` function::

    USER_SUPPORT_ALLOWED = ['can_see_full_profile', 'can_delete_item']

    def central_authorizations(user, codename):
        """
        This function will be called **before** any other rule,
        so you can override all of the permissions here.
        """

        isAuthorized = False

        if user.get_profile().isUberAdmin():
            isAuthorized = True
        elif user.get_profile().isUserSupport() and codename in USER_SUPPORT_ALLOWED:
            isAuthorized = True

        return isAuthorized

As you can imagine, everything that is checked in ``central_authorizations`` is
global to the **whole** project.


Status and testing
==================

django-rules is meant to be a security application. Thus, it has been thoroughly
tested. It comes with a battery of tests that tries to cover all of the
available funcionality. However, if you come across a bug or an irregular
situation, feel free to report it through the `Github bug tracker
<https://github.com/maraujop/django-rules/issues>`_.

Finally, the application comes geared with many different exceptions that will
make sure rules are created properly. They are also aimed to keep the security
of your application away from negligence. Manage the exceptions wisely and you
will be a happy and secure coder, as security is kept away from possible
neglicence. You should manage them carefuly.

Testing django-rules
--------------------

To run tests, get into tests directory and execute::

    ./runtests.py

It should always say OK. If not, there is a broken test that I hope you will be
reporting soon :)


Need more examples?
===================

I have done my best trying to explain the concept behind django-rules but, if
you would rather look at more code examples, I am sure you will find the `code
in the tests
<https://github.com/maraujop/django-rules/blob/master/django_rules/tests/test_core.py>`_
quite useful :)


More Documentation
==================

In case you want to know where all this "per-object authentication backend in
Django" came to exist, you should at least read the following links:

* A great article about `per-object permission backends in Django
  <http://djangoadvent.com/1.2/object-permissions/>`_ by Florian Apolloner
* Also, check the explanation of the changes introduced when fixing the `django
  ticket #11010 <http://code.djangoproject.com/ticket/11010>`_

Finally, my most sincere appreciation goes to everybody that contributes to the
wonderful Django development framework and also to the rest of developers and
committers that build django-rules with their help. Respect! :)
