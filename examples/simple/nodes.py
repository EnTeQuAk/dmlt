#-*- coding: utf-8 -*-
import re
import unicodedata
from urlparse import urlparse, urlunparse
from dmlt.node import Node, Container, Text, HTML
from dmlt.utils import escape, build_html_tag, striptags, lstrip_ext


_slugify_replacement_table = {
    u'\xdf': 'ss',
    u'\xe4': 'ae',
    u'\xe6': 'ae',
    u'\xf0': 'dh',
    u'\xf6': 'oe',
    u'\xfc': 'ue',
    u'\xfe': 'th'
}
_punctuation_re = re.compile(r'[\s!"#$%&\'()*\-/<=>?@\[\\\]^_`{|},;]+')


def slugify(string):
    """Slugify a string."""
    result = []
    for word in _punctuation_re.split(string.strip().lower()):
        if word:
            for search, replace in _slugify_replacement_table.iteritems():
                word = word.replace(search, replace)
            word = unicodedata.normalize('NFKD', word)
            result.append(word.encode('ascii', 'ignore'))
    return u'-'.join(result)


def error_box(title, message):
    """Create an error node."""
    return Error([
        Strong([Text(title)]),
        Paragraph([Text(message)])
    ])


class Newline(Node):
    """
    A newline in a paragraph.  Never use multiple of those.
    """

    text = u'\n'

    def prepare_html(self):
        yield u'<br />'


class Ruler(Node):
    """
    Newline with line.
    """

    def prepare_html(self):
        yield u'<hr />'


class Image(Node):
    """
    Image node.
    """

    def __init__(self, href, alt, id=None, class_=None, style=None):
        self.href = href
        self.alt = alt
        self.id = id
        self.class_ = class_
        self.style = style

    @property
    def text(self):
        return self.alt

    def prepare_html(self):
        yield build_html_tag(u'img', src=self.href, alt=self.alt, id=self.id,
                             class_=self.class_, style=self.style)


class Element(Container):
    """
    Baseclass for elements.
    """

    def __init__(self, children=None, id=None, style=None, class_=None):
        Container.__init__(self, children)
        self.id = id
        self.style = style
        self.class_ = class_

    @property
    def text(self):
        rv = Container.text.__get__(self)
        return rv


class Span(Element):
    """
    Inline general text element
    """

    def __init__(self, children=None, id=None,
                 style=None, class_=None):
        Element.__init__(self, children, id, style, class_)

    def prepare_html(self):
        yield build_html_tag(u'span',
            id=self.id,
            style=self.style,
            class_=self.class_,
        )
        for item in Element.prepare_html(self):
            yield item
        yield u'</span>'


class Link(Element):
    """
    """

    def __init__(self, href, children=None, title=None, id=None,
                 style=None, class_=None):
        self.href = href.strip()
        if title is None:
            title = self.href
        self.title = lstrip_ext(title, num=1)

        if not children:
            children = [Text(self.title)]
        Element.__init__(self, children, id, style, class_)

    def prepare_html(self):
        yield build_html_tag(u'a',
            class_=self.class_,
            rel=self.style=='external' and 'nofollow' or None,
            id=self.id,
            style=self.style,
            title=self.title,
            href=self.href
        )
        for item in Element.prepare_html(self):
            yield item
        yield u'</a>'


class Paragraph(Element):
    """
    A paragraph.  Everything is in there :-)
    (except of block level stuff)
    """

    @property
    def text(self):
        return Element.text.__get__(self) + '\n\n'

    def prepare_html(self):
        yield build_html_tag(u'p', id=self.id, style=self.style,
                             class_=self.class_)
        for item in Element.prepare_html(self):
            yield item
        yield u'</p>'


class Error(Element):
    """
    If a macro is not renderable or not found this is
    shown instead.
    """

    def prepare_html(self):
        yield build_html_tag(u'div',
            id=self.id,
            style=self.style,
            classes=('error', self.class_)
        )
        for item in Element.prepare_html(self):
            yield item
        yield u'</div>'


class Preformatted(Element):
    """
    Preformatted text.
    """
    is_raw = True

    def prepare_html(self):
        yield build_html_tag(u'pre', id=self.id, style=self.style,
                             class_=self.class_)
        for item in Element.prepare_html(self):
            yield item
        yield u'</pre>'


class Headline(Element):
    """
    Represents all kinds of headline tags.
    """

    def __init__(self, level, children=None, id=None, style=None, class_=None):
        Element.__init__(self, children, id, style, class_)
        self.level = level
        if id:
            self.id = slugify(escape(anchor.strip()[1:]))
        else:
            self.id = slugify(escape(self.text))

    def prepare_html(self):
        yield build_html_tag(u'h%d' % (self.level),
            id=self.id,
            style=self.style,
            class_=self.class_
        )
        for item in Element.prepare_html(self):
            yield item
        yield (u'<a title="Link to %s" class="anchor" href="#%s">#</a>'
               % (self.id, self.id))
        yield u'</h%d>' % (self.level)


class Strong(Element):
    """
    Holds children that are emphasized strongly.  For HTML this will
    return a <strong> tag which is usually bold.
    """

    def prepare_html(self):
        yield build_html_tag(u'strong', id=self.id, style=self.style,
                             class_=self.class_)
        for item in Element.prepare_html(self):
            yield item
        yield u'</strong>'


class Emphasized(Element):
    """
    Like `Strong`, but with slightly less importance.  Usually rendered
    with an italic font face.
    """

    def prepare_html(self):
        yield build_html_tag(u'em', id=self.id, style=self.style,
                             class_=self.class_)
        for item in Element.prepare_html(self):
            yield item
        yield u'</em>'


class Code(Element):
    """
    This represents code.  Usually formatted in a monospaced font that
    preserves whitespace.  Additionally this node is maked raw so children
    are not touched by the altering translators.
    """

    def prepare_html(self):
        yield build_html_tag(u'code', id=self.id, style=self.style,
                             class_=self.class_)
        for item in Element.prepare_html(self):
            yield item
        yield u'</code>'


class Underline(Element):
    """
    This element exists for backwards compatibility to MoinMoin and should
    not be used.  It generates a span tag with an "underline" class for
    HTML and could generate something similar for docbook or others.  It's
    also allowed to not render this element in a special way.
    """

    def prepare_html(self):
        yield build_html_tag(u'span',
            id=self.id,
            style=self.style,
            classes=('underline', self.class_)
        )
        for item in Element.prepare_html(self):
            yield item
        yield u'</span>'


class Stroke(Element):
    """
    This element marks deleted text.
    """

    def prepare_html(self):
        yield build_html_tag(u'del', id=self.id, style=self.style,
                             class_=self.class_)
        for item in Element.prepare_html(self):
            yield item
        yield u'</del>'


class Small(Element):
    """
    This elements marks not so important text, so it removes importance.
    It's usually rendered in a smaller font.
    """

    def prepare_html(self):
        yield build_html_tag(u'small', id=self.id, style=self.style,
                             class_=self.class_)
        for item in Element.prepare_html(self):
            yield item
        yield u'</small>'


class Big(Element):
    """
    The opposite of Small, but it doesn't give the element a real emphasis.
    """

    def prepare_html(self):
        yield build_html_tag(u'big', id=self.id, style=self.style,
                             class_=self.class_)
        for item in Element.prepare_html(self):
            yield item
        yield u'</big>'


class Sub(Element):
    """
    Marks text as subscript.
    """

    def prepare_html(self):
        yield build_html_tag(u'sub', id=self.id, style=self.style,
                             class_=self.class_)
        for item in Element.prepare_html(self):
            yield item
        yield u'</sub>'


class Sup(Element):
    """
    Marks text as superscript.
    """

    def prepare_html(self):
        yield build_html_tag(u'sup', id=self.id, style=self.style,
                             class_=self.class_)
        for item in Element.prepare_html(self):
            yield item
        yield u'</sup>'
