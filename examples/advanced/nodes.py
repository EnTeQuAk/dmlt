#-*- coding: utf-8 -*-
from dmlt.inode import Node, Container, Text
from dmlt.utils import escape, build_html_tag


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


class Small(Element):

    def prepare_html(self):
        yield build_html_tag(u'small', id=self.id, style=self.style,
                             class_=self.class_)
        for item in Element.prepare_html(self):
            yield item
        yield u'</small>'


class Big(Element):

    def prepare_html(self):
        yield build_html_tag(u'big', id=self.id, style=self.style,
                             class_=self.class_)
        for item in Element.prepare_html(self):
            yield item
        yield u'</big>'


class Sub(Element):

    def prepare_html(self):
        yield build_html_tag(u'sub', id=self.id, style=self.style,
                             class_=self.class_)
        for item in Element.prepare_html(self):
            yield item
        yield u'</sub>'


class Sup(Element):

    def prepare_html(self):
        yield build_html_tag(u'sup', id=self.id, style=self.style,
                             class_=self.class_)
        for item in Element.prepare_html(self):
            yield item
        yield u'</sup>'
