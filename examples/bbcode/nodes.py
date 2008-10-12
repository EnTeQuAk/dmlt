#-*- coding: utf-8 -*-

from dmlt.inode import Node, Container, Text
from dmlt.utils import escape, build_html_tag


class Newline(Node):
    is_linebreak_node = True

    def prepare_html(self):
        return u'<br />\n'


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


class Emphasized(Element):

    def prepare_html(self):
        yield build_html_tag(u'em', id=self.id, style=self.style,
                             class_=self.class_)
        for item in Element.prepare_html(self):
            yield item
        yield u'</em>'


class Strong(Element):

    def prepare_html(self):
        yield build_html_tag(u'strong', id=self.id, style=self.style,
                             class_=self.class_)
        for item in Element.prepare_html(self):
            yield item
        yield u'</strong>'


class Underline(Element):

    def prepare_html(self):
        yield build_html_tag(u'span',
            id=self.id,
            style=self.style,
            classes=('underline', self.class_)
        )
        for item in Element.prepare_html(self):
            yield item
        yield u'</span>'


class Color(Element):

    def __init__(self, value, children=None, id=None, style=None,
                 class_=None):
        Element.__init__(self, children, id, style, class_)
        self.value = value

    def prepare_html(self):
        style = self.style and self.style + '; ' or ''
        style += 'color: %s' % self.value
        yield build_html_tag(u'span',
            id=self.id,
            style=style,
            class_=self.class_
        )
        for item in Element.prepare_html(self):
            yield item
        yield u'</span>'


class List(Element):
    """
    Sourrounds list items so that they appear as list.  Make sure that the
    children are list items.
    """

    def __init__(self, type, children=None, id=None, style=None, class_=None):
        Element.__init__(self, children, id, style, class_)
        self.type = type

    def prepare_html(self):
        if self.type == 'unordered':
            tag = u'ul'
            cls = None
        else:
            tag = u'ol'
            cls = self.type
        yield build_html_tag(tag, id=self.id, style=self.style,
                             classes=(self.class_, cls))
        for item in Element.prepare_html(self):
            yield item
        yield u'</%s>' % tag


class ListItem(Element):
    """
    Marks the children as list item.  Use in conjunction with list.
    """

    def prepare_html(self):
        yield build_html_tag(u'li', id=self.id, style=self.style,
                             class_=self.class_)
        for item in Element.prepare_html(self):
            yield item
        yield u'</li>'
