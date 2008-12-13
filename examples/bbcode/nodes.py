#-*- coding: utf-8 -*-
from dmlt import events
from dmlt.node import Node as BaseNode, Container as BaseContainer, Text as BaseText
from dmlt.utils import escape, build_html_tag, lstrip_ext


class Node(BaseNode):
    allows_paragraphs = False
    is_paragraph = False
    is_block_tag = False


class Container(Node):
    """
    A basic node with children.
    """
    is_container = True

    def __init__(self, children=None):
        if children is None:
            children = []
        self.children = children

    @property
    def text(self):
        return u''.join(x.text for x in self.children)

    def prepare_html(self):
        for child in self.children:
            for item in child.prepare_html():
                yield item


class Document(Container):
    """
    Outermost node.
    """
    is_document = True
    allows_paragraphs = True

@events.register('define-document-node')
def _handle_define_document_node(manager, *args, **kwargs):
    return Document


class Text(Node):
    """
    Represents text.
    """

    is_text_node = True

    def __init__(self, text=u''):
        self.text = text

    def prepare_html(self):
        yield escape(self.text)


class Newline(Node):
    is_linebreak_node = True

    def prepare_html(self):
        return u'<br />\n'


class Element(Container):
    """
    Baseclass for elements.
    """
    # theese needs to be hooked up because `Container` does not inherit
    # from our self defined `Node`.
    allows_paragraphs = False
    is_paragraph = False
    is_block_tag = False


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


class Paragraph(Element):
    """
    A paragraph.  Everything is in there :-)
    (except of block level stuff)
    """
    is_block_tag = True
    is_paragraph = True
    is_linebreak_node = True

    @property
    def text(self):
        return Element.text.__get__(self).strip() + '\n\n'

    def prepare_html(self):
        yield build_html_tag(u'p', id=self.id, style=self.style,
                             class_=self.class_)
        for item in Element.prepare_html(self):
            yield item
        yield u'</p>'


class List(Element):
    """
    Sourrounds list items so that they appear as list.  Make sure that the
    children are list items.
    """
    is_block_tag = True

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
    is_block_tag = True
    allows_paragraphs = True

    def prepare_html(self):
        yield build_html_tag(u'li', id=self.id, style=self.style,
                             class_=self.class_)
        for item in Element.prepare_html(self):
            yield item
        yield u'</li>'


class Quote(Element):
    """
    A blockquote.
    """
    allows_paragraphs = True
    is_block_tag = True

    def prepare_html(self):
        yield build_html_tag(u'blockquote', id=self.id, style=self.style,
                             class_=self.class_)
        for item in Element.prepare_html(self):
            yield item
        yield u'</blockquote>'


class Link(Element):
    """
    """

    def __init__(self, href, children=None, title=None, id=None,
                 style=None, class_=None):
        self.href = href.strip()
        if not title:
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
