#-*- coding: utf-8 -*-
"""
    dmlt.query
    ~~~~~~~~~~

    This module implements some query interface for nodes.

    :copyright: 2008 by Christopher Grebs.
    :license: BSD, see LICENSE for details.
"""


class NodeQueryMixin(object):
    """
    Adds a `query` property to nodes implementing this interface. The query
    attribute returns a new `Query` object for the node that implements the
    query interface.
    """

    @property
    def query(self):
        return Query((self,))


class Query(object):
    """
    Helper class to traverse a tree of nodes.  Useful for tree processor
    macros that collect data from the final tree.
    """

    def __init__(self, nodes, recurse=True):
        self.nodes = nodes
        self._nodeiter = iter(self.nodes)
        self.recurse = recurse

    def __iter__(self):
        return self

    def next(self):
        return self._nodeiter.next()

    @property
    def has_any(self):
        """Return `True` if at least one node was found."""
        try:
            self._nodeiter.next()
        except StopIteration:
            return False
        return True

    @property
    def children(self):
        """Return a new `Query` just for the direct children."""
        return Query(self.nodes, False)

    @property
    def all(self):
        """Retrn a `Query` object for all nodes this node holds."""
        def walk(nodes):
            for node in nodes:
                yield node
                if self.recurse and node.is_container:
                    for result in walk(node.children):
                        yield result
        return Query(walk(self))

    def by_type(self, type):
        """Performs an instance test on all nodes."""
        return Query(n for n in self.all if isinstance(n, type))

    def text_nodes(self):
        """Only text nodes."""
        return Query(n for n in self.all if n.is_text_node)
