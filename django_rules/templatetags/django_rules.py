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


def _compile_patterns():
    for tag_name, pat in _tag_patterns.iteritems():
        pat = r'^' + tag_name + ' ' + pat
        pat = pat.replace(' ', '(\s)+')
        _patterns[tag_name] = re.compile(pat)

_tag_patterns = {
    'has_perm': r'(?P<user>\w+)? (?P<obj>\w+).(?P<codename>\w+)( as (?P<varname>\w+))?$',
}
_patterns = {}
_compile_patterns()


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
        {% if OBJ_CODENAME %}
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
        bits = _patterns['has_perm'].search(token.contents).groupdict()
    except AttributeError:
        raise template.TemplateSyntaxError("Incorrect 'has_perm' template tag syntax")

    return PermsNode(**bits)
