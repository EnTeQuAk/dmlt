#-*- coding: utf-8 -*-
import re
from dmlt import events
from dmlt.machine import MarkupMachine, Directive, RawDirective, \
                         rule, bygroups
from dmlt.utils import parse_child_nodes, filter_stream
import nodes


_number_re = re.compile(r'\d+(?:\.\d*)?')
_bb_start = r'\[%s\s*%s\]'
_bb_end = r'\[\/%s\]'
_bb_option_parts = r'(?:\=\s*(.*?)\s*)?'
_css_color_names = [
    'aqua', 'black', 'blue', 'fuchsia', 'gray', 'green', 'lime', 'yellow'
    'maroon', 'navy', 'olive', 'purple', 'red', 'silver', 'teal', 'white'
]

_url_pattern = (
    # urls with netloc
    r'(?:(?:https?|ftps?|file|ssh|mms|svn(?:\+ssh)?|git|dict|nntp|irc|'
    r'rsync|smb|apt)://|'
    # urls without netloc
    r'(?:mailto|telnet|s?news|sips?|skype):)')

_free_link_re = re.compile(r'(%s[^\s/]+(/[^\s.,:;?]*([.,:;?][^\s.,:;?]'
                           '+)*)?)(?i)' % _url_pattern)


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


def make_bbcode_end(name, join=False):
    """Just return some [/`name`] expression"""
    return (join and r'|' or r'') + _bb_end % name


def make_bbcode_tag(name, options=False):
    """
    :Parameters:
        `name`
            The name of the tag. E.g, if it's "b"
            the tag will be indentified as [b] and [/b]
        `options`
            Append a regular expression to identify options::
                [tag=option1, option2][/tag]
    """
    expression = _bb_start % (name, options and _bb_option_parts or '')
    return expression


class TextDirective(RawDirective):
    name = 'text'

    def parse(self, stream):
        return nodes.Text(stream.expect('text').value)
@events.register('define-raw-directive')
def _handle_define_raw_Directive(*args, **kwargs):
    return TextDirective


class NewlineDirective(Directive):
    rule = rule(r'\n', enter='nl', one=True)

    def parse(self, stream):
        stream.expect('nl')
        return nodes.Newline()


class SimpleBBCodeDirective(Directive):
    __directive_node__ = None
    name = None

    @property
    def rules(self):
        return [
            rule(make_bbcode_tag(self.name), enter=self.name),
            rule(make_bbcode_end(self.name), leave=self.name)]

    def parse(self, stream):
        dn = self.name
        begin, end = '%s_begin' % dn, '%s_end' % dn
        stream.expect(begin)
        children = parse_child_nodes(stream, self, end)
        stream.expect(end)
        return self.__directive_node__(children)


class StrongDirective(SimpleBBCodeDirective):
    __directive_node__ = nodes.Strong
    name = 'b'


class EmphasizedDirective(SimpleBBCodeDirective):
    __directive_node__ = nodes.Emphasized
    name = 'i'


class UnderlineDirective(SimpleBBCodeDirective):
    __directive_node__ = nodes.Underline
    name = 'u'


class ColorDirective(Directive):
    rules = [
        rule(make_bbcode_tag('color', True), bygroups('color'),
             enter='color'),
        rule(make_bbcode_end('color'), leave='color')
    ]

    def parse(self, stream):
        stream.expect('color_begin')
        color = stream.expect('color').value
        children = parse_child_nodes(stream, self, 'color_end')
        stream.expect('color_end')
        return nodes.Color(color, children)


class ListDirective(Directive):
    rules = [
        rule(make_bbcode_tag('list', True), bygroups('list_type'),
             enter='list'),
        rule(r'\[\*\]\s*(.*)(?m)', bygroups('value'), enter='list_item',
             leave='list_item', one=True),
        rule(make_bbcode_end('list', False), leave='list')
    ]

    def parse(self, stream):
        if stream.test('list_item'):
            # parse list items
            stream.next()
            val = self.machine.dispatch_node(stream)
            return nodes.ListItem([nodes.Text(val)])

        def finish():
            return nodes.List(list_type, children)

        def is_empty_node(node):
            return node.is_linebreak_node or \
                   (node.is_text_node and not node.text.strip())

        def finish_if_list_end():
            if stream.test('list_end'):
                stream.next()
                return finish()

        stream.expect('list_begin')
        t = stream.expect('list_type')
        if not t.value:
            list_type = 'unordered'
        else:
            list_type = {
                '1':    'arabic',
                'a':    'alphalower',
                'A':    'alphalower',
                '*':    'unordered'
            }.get(t.value, None)

        if list_type is None:
            ret = u'[list]' + (u''.join(filter_stream(
                               stream, ('list_end', 'eof'), False)))
            ret += stream.expect('list_end').value
            return nodes.Text(ret)

        children = filter(lambda n: not is_empty_node(n),
                          parse_child_nodes(stream, self, ('list_end', 'eof')))

        # broken markup, no end tags...
        if stream.eof:
            return finish()

        finish_if_list_end()

        return finish()


class QuoteDirective(Directive):
    rules = [
        rule(make_bbcode_tag('quote', True), bygroups('quote_user'),
             enter='quote'),
        rule(make_bbcode_end('quote'), leave='quote')
    ]

    def parse(self, stream):
        stream.expect('quote_begin')
        user = stream.expect('quote_user')
        ret = []

        if user.value is not None:
            u = user.value
            user = u[-1] == ':' and u or u'%s said:' % u
            ret = [nodes.Strong([nodes.Text(user)]), nodes.Newline()]

        children = parse_child_nodes(stream, self, 'quote_end')
        stream.expect('quote_end')
        return nodes.Container(ret + [nodes.Quote(children)])


class UrlDirective(Directive):
    rules = [
        rule(make_bbcode_tag('url', True), bygroups('url_source'),
             enter='url'),
        rule(make_bbcode_end('url'), leave='url'),
    ]

    def parse(self, stream):
        stream.expect('url_begin')
        href = stream.expect('url_source').value
        children = parse_child_nodes(stream, self, 'url_end')
        title = children and u''.join(n.text for n in children)
        if href is None:
            href = title
        stream.expect('url_end')
        return nodes.Link(href, children, title)


class BBCodeMarkupMachine(MarkupMachine):
    directives = [StrongDirective, EmphasizedDirective,
                  UnderlineDirective, ColorDirective, ListDirective,
                  QuoteDirective, UrlDirective]
    restrictive_mode = True


TESTTEXT = u'''\
bold: [b]bold[/b]
italic: [i]italic[/i]
underline: [u]underline[/u]
color: [color=red][color=blue]red text[/color][/color]
[list]
[*] Item
[*] Item2
[/list]
[list=1]
[*] [b]enum 1[/b]
[*] enum 2
[/list]
[quote=some user]Ich bin ein testtext

[b][b]mööp[/b][/b]
[/quote]
[quote]Ich bin ein weiterer Testtext[/quote]
[url=http://ichbineinlink.xy]Text[/url]
[url]http://somelink.xy[/url]
[url=ftp://anotherlink.de][/url]

[list] [*] Foo [/list] [quote] [/list]
'''
text = TESTTEXT

def main():
    print u'\n'.join(repr(x) for x in BBCodeMarkupMachine(text).tokenize())
    stream = BBCodeMarkupMachine(text).stream
    stream.debug()
    print "#####################################################\n\n\n\n"
    print BBCodeMarkupMachine(text).render(enable_escaping=False)
