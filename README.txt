h1. Django-rules

Django-rules is a Django authorization backend for unified per object permission management. This is supported since Django 1.2 and It will not work with older Django releases.

h2. Installation

To install Django-rules run:
<code>python setup.py install</code>

h2. Configuration

You need to hook it into your project:
<b>1.</b> Put into your `INSTALLED_APPS` at settings:
<pre> 
INSTALLED_APPS = {
    ...
    'django_rules',
}
</pre>

<b>2.</b> Add it as an authorization backend:
<pre> 
AUTHENTICATION_BACKENDS = {
    'django.contrib.auth.backends.ModelBackend', # default
    'django_rules.backends.ObjectPermissionBackend',
)
</pre>

h2. Usage

Django-rules differ from other authorization backends in the way it lets you flexibly manage per object permissions. Every rule is associated to a method 
that corresponds to a model. That method will be in charge of checking if the user has authorization to take an action over an object. 

h3. Creating rules

You will have to create a rules.py file under every Django-app's directory in which you want to create rules. 
rules.py should contain the rule declarations for only that application. Every rule is formed by 6 parameters: 
<ul>
<li><b>app_name:</b> Name of the app to which the rule belongs to.</li>
<li><b>codename:</b> This is the name of the rule and has to be unique among all applications.</li>
<li><b>model:</b> This the name of the model that the rule is associated to.</li>
<li><b>field_name: (Optional)</b> This is the name of the model's method, property or field that the rule is associated to. If you don't set it, the codename will be used as default</li>
<li><b>view_param_pk: (Optional)</b> This is necessary if you use the decorator that comes with this app. It is the view's param that will be used as primary key value for getting the object of that model. If you don't set it, the model's primary key field name will be used by default.</li>
<li><b>description: (Optional)</b> 140 characters to explain what the rule if for in readable text.</li>
</ul>

You will have to call `django.utils.register` for each rule you want to be effective. 

h3. Example

I'm going to show a complete example, using the next model to elaborate it:

<code>
class Dummy(models.Model):
    idDummy = models.AutoField(primary_key = True)
    supplier = models.ForeignKey(User, null = False)

    def canShip(self,user_obj):
        """
        Only the supplier can_ship in our business logic.
        Checks if the user_obj passed is the supplier.
        """
        return self.supplier == user_obj
</code>

This is how a rules.py with only one effective rule looks like:

<code>
from django_rules import utils

rules_list = [
    {'codename':'can_ship','field_name':'canShip', 'model':'dummy', 'view_param_pk':'idView', 'description':"Rule that checks if the user is a supplier"},
    
    # same rule but with subtle changes. It is commented, so it will not be effective
    # {'codename':'canShip', 'model':'dummy', 'view_param_pk':'idView', 'description':"Rule that checks if the user is a supplier"},
    
    # same rule, but now 'idDummy' will be used for view_param_pk. This is the more compact style possible
    # {'codename':'canShip', 'model':'dummy'},
]

# Now we have to register the rules so they are effective
for params in rules_list:
    utils.register(app_name="shipping", **params)
<code>

h3. Syncing rules

Next step would be to sync those rules. In your Django project you will have to run sync_rules command doing:
<code>python manage.py sync_rules</code>

This command will look for all your rules.py files under your `INSTALLED_APPS and sync the Database with the last changes, so you don't have to run `syncdb` or drop the database before.

h3. Using rules

Whenever you want to check if a user has authorization to take an action over an object. You will need a `contrib.auth.models.User` and of course a model instance. 
To make this clearer suppose there is data in the DB, I'm also omitting imports. In you code you would do:

<code>
user = User.objects.get(pk = 1)
dummy_obj = Dummy.objects.get(pk = 1)

if user.has_perm('can_ship', dummy_object):
    print "Yey! Authorization checking passed"
</code>

This is when all the magic happens, so focus. When you call has_perm Django handles control over django-rules backend. This will call `dummy_object.canShip(user)` if that method returns True, then you have authorization, otherwise you don't.

h3. More on rules

If you have read this carefully, you will be thinking that if the field_name is a method it needs to have a parameter. Well, not completely true. The backend is "smart" and 
it will find out if the method is expecting a parameter or not. In any case, the method maximum number of parameters is one, and that one will be passed and should expect a user object.

You can create rules on model's attributes and properties too. 

h3. Decorators

If you remember every rule has a view_param_pk That is the name of the view's parameter whose value will use the decorator to obtain a rule's model instance.
If you like Python as I do, you will love decorators. As Django has a `permission_required` decorator, this app has an `object_permission_required` decorator. This is how you have to use it:

<pre>
from django_rules import object_permission_required

@object_permission_required('can_ship')
def dummy_view(request, idView):
    return HttpResponse('success')
</pre>

This decorator essentially does: 

<pre>
request.user.has_perm('can_ship', Model.objects.get(pk=idView))
</pre>

You can pass it 3 arguments: 
<pre>@object_permission_required('can_ship', return_403=True)</pre>
<pre>@object_permission_required('can_ship', login_url='/foobar/')</pre>
<pre>@object_permission_required('can_ship', redirect_field_name='/whatever/')</pre>

By default `return_403` is set to False, `redirect_field_name` to an emtpy string and If the user has no rights, it will redirect to `settings.LOGIN_URL`

h3. Centralized Permissions

Everyone's got a web application that has special privileged groups like administrators, user support or staff. `django-rules` has a way to let you bypass authorization system for whatever reasons you have. You will need to set in your project settings the variable CENTRAL_AUTHORIZATIONS pointing to a module:

<pre>
CENTRAL_AUTHORIZATIONS = 'project.utils'
</pre>

In that module you will need to define a homonym function, that has to expect 2 parameters. First a user object, second a permission codename:

<pre>
def central_authorizations(user_obj, perm):
    # Here you can do anything you want, this will be checked before any other rule
    if user_obj.get_profile().isUserSupport() and perm in ['whatever']:
        return True
    [...]
</pre>

Only requesite, as you have probably imagined, is that the function has to return a boolean value. As you can imagine, everything that is checked in central_authorizations is global to the whole project.

h2. Philosophy 

Behind django-rules there is the idea of building a flexible and scalable authorization backend. Why is it better?

<ul>
<li>First, you can change a method code whenever, changing how permissions work at any time. It's dynamic and you know dynamic sounds way better than static</li>
<li>You don't need to add permissions to anybody, permissions are implicit, it kind of works like roles, though these are rules :)</li>
<li>Some other per object backends create a row in a table for every object, every user and every permission combination. If you have a medium to large site, you are basically screwed, no matter how much you use caching systems.</li>
<li>Other authorization backends have to SELECT all permissions that a user has to answer if the user has only one specific, making the memory footprint bigger.</li>
<li>Some don't have a way to set centralized permissions, which are a real deal in web developing</li>
<li>django-rules backend has way more less lines than others. Less lines makes it faster and less error prone.</li>
</ul>

However, you need to be aware of something. The methods mapped to rules, will be called from now on rule methods. These rule methods should never call any other model's methods. This is to avoid infinite loops. Imagine a situation in which the rule method calls a method that checks for the same authorization, then you have an infinite loop. You may be thinking you can control this, but trust me, it will get very difficult to mantain and scale. Because things will always not be that simple, maybe you call a method that calls a helping function that triggers the same authorization. Indirection gets horrible. In other words "Great power comes with great responsibility"

h2. Status and testing

As django-rules is a security application, it has been thoroughly tested. It comes with a battery of tests, that try to cover all funcionality. However, if you come across a bug or an irregular situation, feel free to report at Github bug tracker.

To run tests, get into tests directory and execute. It should always say OK, if not please report it:
<pre>
./runtests.py
</pre>

The application comes geared with many different exceptions, that will make sure rules are created properly and security is kept away from neglicence. You should manage them carefuly. 

h2. More Documentation

There is a "great article by Florian Apolloner":http://djangoadvent.com/1.2/object-permissions/ about per object permission backends
In this article the author explains how to take advantage of the changes he introduced fixing "ticket 11010":http://code.djangoproject.com/ticket/11010
Here I want to thank him his wonderful job in Django and also to the rest of developers and committers that make Django rule :D

