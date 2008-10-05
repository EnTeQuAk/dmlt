#-*- coding: utf-8 -*-
import re
from dmlt.machine import MarkupMachine, Directive, RawDirective, \
                         rule, bygroups
from dmlt.utils import parse_child_nodes
import nodes


_number_re = re.compile(r'\d+(?:\.\d*)?')

_css_color_names = [
    'aqua', 'black', 'blue', 'fuchsia', 'gray', 'green', 'lime', 'yellow'
    'maroon', 'navy', 'olive', 'purple', 'red', 'silver', 'teal', 'white'
]


class Value(object):

    def __init__(self, value):
        self.value = value

    def __float__(self, default=0.0):
        this = self.value
        if isinstance(this, (int, long, float)):
            return float(this)
        elif isinstance(this, basestring):
            m = number_re.search(this)
            if m:
                return float(m.group())
        return default

    def __int__(self):
        return int(self.__float__(0))

    def __len__(self):
        if self.value:
            return len(self.value)
        return 0

    def __str__(self):
        return str(unicode(self.value))

    def __unicode__(self):
        return unicode(self.value)

    @property
    def is_string(self):
        return not isinstance(self.value, (tuple, list, dict))

    @property
    def is_number(self):
        invalid = object()
        rv = self.__float__(invalid)
        return rv is not invalid

    def __repr__(self):
        return '%s(%r)' % (
            self.__class__.__name__,
            self.value
        )


def parse_options(string):
    items = None
    if ',' in string:
        items = []
        # we assume that this is a list
        for item in string.split(','):
            item = Value(item.strip())
            if item.is_number:
                items.append(item.__float__(0.0))
            elif item.is_string:
                items.append(unicode(item))
    return items or string


def make_bbcode_tag(name, options=False):
    option_parts = r'\=\s*(.*?)\s*'
    expression = r'\[%s\s*%s\]|\[\/%s\]' % (name,
        options and option_parts or '', name)
    print expression
    return expression


class TextDirective(RawDirective):
    name = 'text'

    def parse(self, stream):
        return nodes.Text(stream.expect('text').value)


class SimpleBBCodeDirective(Directive):
    __directive_node__ = None

    def parse(self, stream):
        dn = self.rule.enter
        begin, end = '%s_begin' % dn, '%s_end' % dn
        stream.expect(begin)
        children = parse_child_nodes(stream, self, end)
        stream.expect(end)
        return self.__directive_node__(children)


class StrongDirective(SimpleBBCodeDirective):
    __directive_node__ = nodes.Strong
    rule = rule(make_bbcode_tag('b'), enter='b')


class EmphasizedDirective(SimpleBBCodeDirective):
    __directive_node__ = nodes.Emphasized
    rule = rule(make_bbcode_tag('i'), enter='i')


class UnderlineDirective(SimpleBBCodeDirective):
    __directive_node__ = nodes.Underline
    rule = rule(make_bbcode_tag('u'), enter='u')


class ColorDirective(Directive):
    rule = rule(make_bbcode_tag('color', True), bygroups('color'),
                enter='color')

    def parse(self, stream):
        stream.expect('color_begin')
        color = stream.expect('color').value
        children = parse_child_nodes(stream, self, 'color_end')
        stream.expect('color_end')
        #XXX: I have no idea how to invalidate the next `color` token...
        stream.next()
        return nodes.Color(color, children)


class BBCodeMarkupMachine(MarkupMachine):
    directives = [StrongDirective, EmphasizedDirective, UnderlineDirective,
                  ColorDirective]

    special_directives = [TextDirective]



TESTTEXT = u'''\
bold: [b]bold[/b]
italic: [i]italic[/i]
underline: [u]underline[/u]
color: [color=red]red text[/color]
'''
text = TESTTEXT

if __name__ == '__main__':
    print make_bbcode_tag('b')
    stream = BBCodeMarkupMachine(text).stream
    stream.debug()
    print BBCodeMarkupMachine(text).render(enable_escaping=False)
