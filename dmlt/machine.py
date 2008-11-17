#-*- coding: utf-8 -*-
"""
    dmlt.machine
    ~~~~~~~~~~~~

    Interface for parsing, lexing and node-tree-processing.

    :copyright: 2008 by Christopher Grebs.
    :license: BSD, see LICENSE for more details.
"""
import re
from itertools import izip
from dmlt.errors import MissingContext
from dmlt.datastructure import TokenStream, Context


def bygroups(*args):
    return lambda m: izip(args, m.groups())


class rule(object):
    """
    Represents one parsing rule.
    """
    __slots__ = ('match', 'token', 'enter', 'leave', 'one')

    def __init__(self, regexp, token=None, enter=None, leave=None,
                 one=False):
        self.match = re.compile(regexp, re.U).match
        self.token = token
        self.enter = enter
        self.leave = leave
        self.one = one

    def __repr__(self):
        return '<rule(%s, %s -> %s)>' % (
            self.token,
            self.enter,
            self.leave
        )


class Directive(object):
    """
    A directive that represents a part of the markup language.
    It's used to create a tokenstream and process that stream
    into a node tree.
    """
    rule = None

    def __init__(self, machine, escaping_enabled=False):
        self.machine = machine
        self.ctx = Context(machine, escaping_enabled)

    @property
    def rules(self):
        return [self.rule]

    def parse(self, stream):
        """
        Process the directive and returns some nodes

        If the return value is `None` the node is ignored at all
        and not shown in the output.
        """

    parse_eoc = None

    def __repr__(self):
        return '%s(%r)' % (
            self.__class__.__name__,
            self.rules
        )


class RawDirective(Directive):
    name = 'raw'

    def parse(self, stream):
        """Process raw data"""
        from dmlt.inode import Text
        return Text(stream.current.value)


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


class StreamFilter(object):
    """Baseclass for all stream filters."""

    def process(self, stream, ctx):
        """
        This method is allowed to modify the token stream as needed.
        It can be used to order some tokens that are hard to parse
        with regular expressions.
        Mostly it's more safe to return a new TokenStream instance
        as TokenStream has no defined behaviour with many pushed
        tokens.
        """
        return stream


class NodeFilter(object):
    """Baseclass for all node filters."""

    def process(self, tree, ctx):
        """
        This method is called at the end of the node-tree-processing
        to modify the tree in place. It's also safe to return a new tree.
        """
        return tree


class MarkupMachine(object):
    """
    The markup machine is the heart of DMLT.
    It's used to process a document into a `TokenStream`
    which is used to create a AST (Abstract Syntax Tree) or
    called node-tree that represents the parsed document
    in an abstract form.
    """

    directives = []
    special_directives = []
    text_directive = RawDirective
    raw_name = text_directive.name

    # stream filters
    stream_filters = []

    # node filters
    node_filters = []

    # token-stack-state names. They're defined here so
    # that it's possible to overwrite them
    _begin = '_begin'
    _end = '_end'

    # Default character for escaping markup tokens
    # NOTE: this needs
    escape_character = '\\'

    #
    __document_node__ = None

    def __init__(self, raw):
        self.raw = raw
        self._stream = None
        # process special directives to init some special features
        self._process_special_directives()

    def __repr__(self):
        return '<MarkupMachine(%s)>' % u', '.join(self.directives)

    def _process_special_directives(self):
        """Process directives that hooks some some special into the machine"""
        for directive in self.special_directives:
            #: raw directive
            if RawDirective in directive.__bases__:
                self.text_directive = directive(self)
                self.raw_name = self.text_directive.name

    def _process_lexing_rules(self, raw, enable_escaping=False):
        """
        Process the raw-document with all lexing
        rules and create a tokenstream that can be used for
        further processing.

        :param raw: The raw document.
        :return: A generator object that yields (type, value, directive)
                 tuples which can be mapped into a `Token` instance.
        """
        escaped = False
        pos = d = 0
        end = len(raw)
        text_buffer = []
        add_text = text_buffer.append
        flatten = u''.join
        stack = {}
        lexing_items = []
        for d in (x(self, enable_escaping) for x in self.directives):
            rules = d.rules is not None and d.rules or [d.rule]
            lexing_items.extend([(r, d) for r in rules])
        del d

        while pos < end:
            for rule, directive in lexing_items:
                m = rule.match(raw, pos)
                if m is not None:
                    # handle escaped tokens
                    if escaped:
                        add_text(m.group())
                        pos = m.end()
                        escaped = False
                        break

                    # flush text from the text_buffer
                    if text_buffer:
                        text = flatten(text_buffer)
                        if text:
                            yield self.raw_name, text, self.text_directive
                        del text_buffer[:]

                    if rule.enter is not None or rule.leave is not None:
                        enter, leave = rule.enter, rule.leave
                        if enter is not None and enter in stack:
                            # one rule matches twice, once for the beginning and once
                            # for the end of it's context.
                            del stack[enter]
                            token = enter + self._end
                            yield token, m.group(), directive, True
                        elif enter is not None and not rule.one:
                            # enter a new context
                            stack[enter] = rule
                            token = enter + self._begin
                            yield token, m.group(), directive, False
                        elif not enter in stack and rule.one:
                            # the rule is a standalone one so just yield
                            # the enter point and leave the context
                            yield enter, m.group(), directive, True
                        elif leave is not None and leave in stack:
                            # this rule is some quit-point to jump out of this context
                            del stack[leave]
                            token = leave + self._end
                            yield token, m.group(), directive, True
                        elif leave is not None and leave not in stack:
                            raise MissingContext(u'cannot leave %r' % leave)

                    # process some callables like `bygroups`
                    if callable(rule.token):
                        for item in rule.token(m):
                            yield item
                    elif rule.token is not None:
                        yield rule.token, m.group(), directive, False

                    pos = m.end()
                    break
            else:
                char = raw[pos]
                if enable_escaping:
                    if char == self.escape_character:
                        if escaped:
                            escaped = False
                        else:
                            escaped = True
                            char = ''
                    else:
                        if escaped:
                            char = self.escape_character + char
                        escaped = False
                add_text(char)
                pos += 1

        # if there is a bogus escaped push a backslash
        if escaped:
            add_text(self.escape_character)

        # if the text buffer is left filled, we flush it
        if text_buffer:
            text = flatten(text_buffer)
            if text:
                yield self.raw_name, text, self.text_directive

    def tokenize(self, raw=None, enable_escaping=False):
        """
        Tokenize the raw document, apply stream-filters
        and return the processing-ready token stream.

        :param raw: The raw document.
        :return: A `TokenStream` instance.
        """
        ctx = Context(self, enable_escaping)
        stream = TokenStream.from_tuple_iter(self._process_lexing_rules(
            raw or self.raw, enable_escaping))

        for filter_ in self.stream_filters:
            if not isinstance(filter_, StreamFilter):
                raise RuntimeError('%r filter is no %r instance'
                    % (type(filter_), StreamFilter))
            stream = filter_.process(stream, ctx)
        return stream

    def parse(self, stream=None, inline=False, enable_escaping=False):
        """
        Parse an existing stream or the current `raw` document,
        apply node-filters and return a node-tree.

        :param stream:  An existing stream. If `None` the `raw` attribute
                        is processed into a `TokenStream`.
        :param inline:  If `True` only child-nodes are returned and no
                        `Document` node as the top level one.
        :return:        A node-tree that represents the finished document
                        in an abstract form.
        """
        from dmlt.inode import Document
        if stream is None:
            stream = self.tokenize(enable_escaping=enable_escaping)

        # create the node-tree
        if self.__document_node__ is None:
            document = Document()
        else:
            document = self.__document_node__()

        while not stream.eof:
            node = self.dispatch_node(stream)
            if node is not None:
                document.children.append(node)
            else:
                stream.next()

        # apply node-filters
        ctx = Context(self, enable_escaping)
        for filter_ in self.node_filters:
            if not isinstance(filter_, NodeFilter):
                raise RuntimeError('%r filter is no %r instance'
                    % (type(filter_), NodeFilter))
            document = filter_.process(document, ctx)

        if inline:
            return document.children
        return document

    def dispatch_node(self, stream):
        """
        Dispatch the current node from the `stream`
        """
        directive = stream.current.directive
        if directive is None:
            raise TypeError('Missing directive in stream for token `%s`'
                            % stream.current.type)
        if stream.current.end_of_context and directive.parse_eoc is not None:
            return directive.parse_eoc(stream)
        return directive.parse(stream)

    def render(self, tree=None, format='html', enable_escaping=False):
        """
        Process a given `tree` or the current `raw` document
        into the given output`format`.

        :param tree: A tree that should be processed.
        :param format: The output format to return.
        """
        if tree is None:
            tree = self.parse(enable_escaping=enable_escaping)
        return u''.join(tree.prepare(format))

    ## Some property definitions for an easy-to-use interface
    def _get_stream(self):
        if self._stream is None:
            self._stream = self.tokenize()
        return self._stream
    def _set_stream(self, value):
        self._stream = value
    stream = property(_get_stream, _set_stream)
