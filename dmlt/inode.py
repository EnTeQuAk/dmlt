#-*- coding: utf-8 -*-
"""
    dmlt.inodes
    ~~~~~~~~~~~

    Node interface for DMLT.

    :copyright: 2008 by Christopher Grebs.
    :license: BSD, see LICENSE for more details.
"""
from dmlt.machine import NodeQueryMixin
from dmlt.utils import node_repr, escape, striptags


class BaseNode(object):
    """
    A node that represents a part of a document.
    It still implements the `Query` interface to query for nodes.
    Should be subclassed to implement more `format` options.
    """
    __slots__ = ()

    #: The node can contain children.
    #: Each container node needs to implement
    #: a `children` attribute to access child-nodes.
    is_container = False

    #: True if this is a text node
    is_text_node = False

    #: True if this node is a raw one.
    #: Raw nodes are never processed by node-filters.
    #: Use this only if the node-content matters e.g.
    #: in sourcecode.
    is_raw = False

    is_document = False

    #: the value of the node as text
    text = u''

    def __eq__(self, other):
        return self.__class__ is other.__class__ and \
               self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self.__eq__(other)

    __repr__ = node_repr


class Node(BaseNode, NodeQueryMixin):

    def prepare(self, format='html'):
        return {'html': self.prepare_html}[format]()

    def prepare_html(self):
        return iter(())


class DeferredNode(Node):
    """
    Special node with a `replace_by()` function that can be used to replace
    this node in place with another one.
    """

    def __init__(self, node):
        self.node = node

    def replace_by(self, other):
        self.__class__ = other.__class__
        self.__dict__ = other.__dict__

    is_container = property(lambda s: s.node.is_container)
    is_text_node = property(lambda s: s.node.is_text_node)
    is_raw = property(lambda s: s.node.is_raw)


class Text(Node):
    """
    Represents text.
    """

    is_text_node = True

    def __init__(self, text=u''):
        self.text = text

    def prepare_html(self):
        yield escape(self.text)


class HTML(Node):
    """
    Raw HTML snippet.
    """

    def __init__(self, html=u''):
        self.html = html

    @property
    def text(self):
        return striptags(self.html)

    def prepare_html(self):
        yield self.html


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


class Raw(Container):
    """
    A raw container.
    """
    is_raw = True
