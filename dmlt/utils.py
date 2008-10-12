#-*- coding: utf-8 -*-
"""
    dmlt.utils
    ~~~~~~~~~~

    Some often used utilities for text processing.

    :copyright: 2006-2008 by Christopher Grebs
    :license: BSD, see LICENSE for more details.
"""
import re
import locale
from cPickle import loads, dumps, HIGHEST_PROTOCOL
from htmlentitydefs import name2codepoint
from xml.sax.saxutils import quoteattr

_html_entities = name2codepoint.copy()
_html_entities['apos'] = 39
_html_entity_re = re.compile(r'&([^;]+);')
#: set of tags that don't want child elements.
EMPTY_TAGS = set(['br', 'img', 'area', 'hr', 'param', 'meta', 'link', 'base',
                  'input', 'embed', 'col', 'frame', 'spacer'])
_entity_re = re.compile(r'&([^;]+);')
_strip_re = re.compile(r'<!--.*?-->|<[^>]*>(?s)')
del name2codepoint


def to_unicode(string, charset=None):
    """
    Decode a ``string`` to ``charset``.

    If ``charset`` is ``None`` utf-8 is used as the default.
    """
    if isinstance(string, unicode):
        # return unicode objects as is.
        return string
    if charset is not None:
        # try to decode with the given 'charset'
        return string.decode(charset, 'replace')
    else:
        try:
            # decode with utf-8
            return string.decode('utf-8')
        except UnicodeError:
            try:
                # if utf-8 encoding doesn't work try the local preferred one
                return string.decode(locale.getpreferredencoding(), 'replace')
            except UnicodeError:
                # if nothing work... fallback to 'iso-8859-15'
                return string.decode('iso-8859-15', 'replace')


def encode(string, charset='utf-8'):
    """Encode ``string`` to ``charset``"""
    return to_unicode(string).encode(charset)


def escape(val, quote=False):
    """
    SGML/XML escape an unicode object.
    """
    if val is None:
        return ''
    elif not isinstance(val, basestring):
        val = unicode(val)
    val = val.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    if not quote:
        return val
    return val.replace('"', '&quot;')


def unescape(val):
    """
    The reverse function of `escape`. This unescapes all the HTML
    entities, not only the XML ones inserted by `escape`.
    """
    def handle_match(m):
        name = m.group(1)
        if name in _html_entities:
            return unichr(_html_entities[name])
        try:
            if name[:2] in ('#x', '#X'):
                return unichr(int(name[2:], 16))
            elif name.startswith('#'):
                return unichr(int(name[1:]))
        except ValueError:
            pass
        return u''
    return _html_entity_re.sub(handle_match, val)


def rstrip_ext(string, chars=None, num=None):
    """
    rstrip_ext(string [,chars, num]) -> string

    Return a copy of the string s with trailing chars removed.
    If chars is given and not None, remove characters in chars instead.
    If num is given and not None, remove max. num characters if given,
    whitespaces if not.
    """
    if chars is None:
        chars = u' '

    if num is None:
        return string.rstrip(chars)

    result = list(string)
    for i, char in enumerate(reversed(string)):
        if char in chars and i < num:
            result.pop()
    return u''.join(result)


def lstrip_ext(string, chars=None, num=None):
    """
    lstrip_ext(string [,chars, num]) -> string

    Return a copy of the string `string` with leading chars removed.
    If `chars` is given and not `None`, remove characters in `chars` instead.
    If `num` is given and not `None`, remove max. `num` characters if given,
    whitespaces if not.
    """
    if chars is None:
        chars = u' '

    if num is None:
        return string.lstrip(chars)

    result = list(string)
    for i, char in enumerate(string):
        if char in chars and i < num:
            result.pop(0)
    return u''.join(result)


def strip_ext(text, chars=None, num=None):
    """
    strip_ext(s [,chars, num]) -> string

    Return a copy of the string s with leading and trailing
    chars removed.
    If chars is given and not None, remove characters in chars instead.
    If num is given and not None, remove max. num characters if given, whitespaces
    if not.
    """
    if chars is None:
        chars = u' '

    if num is None:
        return text.strip(chars)

    return lstrip_ext(rstrip_ext(text, chars, num), chars, num)


def node_repr(obj):
    """
    A function that does a debug repr for an object. This is used by all the
    `nodes` so that we get a debuggable ast.
    """
    return '%s.%s(%s)' % (
        obj.__class__.__module__.rsplit('.', 1)[-1],
        obj.__class__.__name__,
        ', '.join('%s=%r' % (key, value)
        for key, value in sorted(getattr(obj, '__dict__', {}).items()))
    )


def parse_child_nodes(stream, node, until):
    """
    Get some child nodes from `stream` until `until` is reached.

    The `stream` is stripped by all passed tokens except the
    `until`-type one so that you can `stream.expect` this token type.
    """
    children = []
    while 1:
        if isinstance(until, (list, tuple)):
            if stream.current.type in until: break
        else:
            if stream.current.type == until: break
        children.append(node.machine.dispatch_node(stream))
    return children


def filter_stream(stream, until, pop_none=True):
    """
    Get some child-values from `stream` until `until` is reached

    The `stream` is stripped by all passed tokens except the `until`-type
    one so that you can `stream.expect` this token type.
    """
    buffer = []
    while 1:
        if isinstance(until, (list, tuple)):
            if stream.current.type in until: break
        else:
            if stream.current.type == until: break

        if pop_none and stream.current.directive is None:
            stream.next()
            continue
        if stream.current.value:
            buffer.append(stream.current.value)
        stream.next()
    return buffer


def dump_tree(tree, format):
    """
    Dump ``tree`` with the help of pickle.

    :param tree: The node-tree to pickle.
    :param format: the output format that tree represents.
    """
    assert not '\0' in format
    result = []
    text_buffer = []
    is_dynamic = False

    for item in tree.children:
        if isinstance(item, basestring):
            text_buffer.append(item)
        else:
            if text_buffer:
                result.append(u''.join(text_buffer))
                del text_buffer[:]
            result.append(item)
            is_dynamic = True
    if text_buffer:
        result.append(u''.join(text_buffer))

    if not is_dynamic:
        return '!%s\0%s' % (format, u''.join(result).encode('utf-8'))
    return '@' + dumps((format, result), HIGHEST_PROTOCOL)


def load_tree(obj):
    """
    Load a node-tree from ``object``.

    ``object`` can be a node-tree (than it's just returned)
    or a string-instance dumped by `dump_tree`.

    :return: A tuple in the form of (instructions, node, format).
    """
    if isinstance(obj, str):
        node = None
        if obj[0] == '!':
            pos = obj.index('\0')
            format = obj[1:pos]
            instructions = [obj[pos+1:].decode('utf-8')]
        elif obj[0] == '@':
            format, instructions = loads(obj[1:])
    else:
        instructions = format = None
        node = obj
    return (instructions, node, format)


def _build_html_tag(tag, attrs):
    """Build an HTML opening tag."""
    attrs = u' '.join(iter(
        u'%s=%s' % (k, quoteattr(unicode(v)))
        for k, v in attrs.iteritems()
        if v is not None
    ))
    return u'<%s%s%s>' % (
        tag, attrs and ' ' + attrs or '',
        tag in EMPTY_TAGS and ' /' or ''
    ), tag not in EMPTY_TAGS and u'</%s>' % tag or u''


def build_html_tag(tag, class_=None, classes=None, **attrs):
    """Build an HTML opening tag."""
    if classes:
        class_ = u' '.join(x for x in classes if x)
    if class_:
        attrs['class'] = class_
    return _build_html_tag(tag, attrs)[0]


def replace_entities(string):
    """
    Replace HTML entities in a string:

    >>> replace_entities('foo &amp; bar &raquo; foo')
    ...
    """
    def handle_match(m):
        name = m.group(1)
        if name in _html_entities:
            return unichr(_html_entities[name])
        if name[:2] in ('#x', '#X'):
            try:
                return unichr(int(name[2:], 16))
            except ValueError:
                return u''
        elif name.startswith('#'):
            try:
                return unichr(int(name[1:]))
            except ValueError:
                return u''
        return u''
    return _entity_re.sub(handle_match, string)


def striptags(string):
    """Remove HTML tags from a string."""
    return replace_entities(u' '.join(_strip_re.sub('', string).split()))


def flatten_iterator(iter):
    """Flatten an iterator to one without any sub-elements"""
    for item in iter:
        if hasattr(item, '__iter__'):
            for sub in flatten_iterator(item):
                yield sub
        else:
            yield item
