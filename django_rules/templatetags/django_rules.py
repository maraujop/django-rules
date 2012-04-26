# -*- coding: utf-8 -*-
import re

from django import template
register = template.Library()


class PermsNode(template.Node):
    def __init__(self, codename, obj, user=None, varname=None):
        self.codename = codename
        self.obj = obj
        self.user = 'user' if user is None else user
        self.varname = "%s_%s" % (obj, codename) if varname is None else varname

    def render(self, context):
        user = template.resolve_variable(self.user, context)
        obj = template.resolve_variable(self.obj, context)
        context[self.varname] = user.has_perm(self.codename, obj)
        return ''


@register.tag
def has_perm(parser, token):
    """
    Template tag to check object permissions.

    Usage:
     * loading:
        {% load has_perm %}

     * Example 1: explicit user:
        {% has_perm USER OBJ.CODENAME %}

     * Example 2: implicit user (USER is the 'user' object in context)
        {% has_perm OBJ.CODENAME %}

     Then, you can do:
        {% if CODENAME %}
            (...)
        {% endif %}

    Note that all these modes support appending 'as VARNAME'
        {% has_perm OBJ.CODENAME as VARNAME %}

    so you can use VARNAME in the IF clauses instead of using CODENAME
        {% if VARNAME %}
            (...)
        {% endif %}
    """
    try:
        SPACES_PATTERN = '(\s)+'
        pat = r'^has_perm ' + \
              r'(?P<user>\w+)? (?P<obj>\w+).(?P<codename>\w+)' + \
              r'(' + \
                r' as ' + \
                  r'(?P<varname>\w+)' + \
              r')?$'
        pat = pat.replace(' ', SPACES_PATTERN)
        bits = re.search(pat, token.contents).groupdict()
    except AttributeError:
        raise template.TemplateSyntaxError("Incorrect 'has_perm' template tag syntax")

    return PermsNode(**bits)
