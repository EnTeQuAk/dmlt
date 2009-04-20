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
from collections import deque
from dmlt import events, node
from dmlt.exc import MissingContext
from dmlt.utils import AdvancedDefaultdict
from dmlt.datastructure import TokenStream, Context


__all__ = ('bygroups', 'rule', 'Directive', 'MarkupMachine')



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
        ret = stream.current.value
        stream.next()
        return node.Text(ret)

@events.register('define-raw-directive')
def _handle_define_raw_directive(manager, *args, **kwargs):
    return RawDirective


class MarkupMachine(object):
    """
    The markup machine is the heart of DMLT.
    It's used to process a document into a `TokenStream`
    which is used to create a AST (Abstract Syntax Tree) or
    called node-tree that represents the parsed document
    in an abstract form.
    """
    # token-stack-state names. They're defined here so
    # that it's possible to overwrite them
    _begin = '_begin'
    _end = '_end'

    escape_character = '\\'

    # The restrictive mode is some special feature that enables
    # dmlt to manage the stack itselfs. That way every state that
    # was opened right after state quo will be announced and closed
    # as well. Set this to `False` it you don't wanna matter about that.
    # If it is disabled dmlt is looking for the last entry for the state
    # that needs to be closed in the stack and just removes it. All other
    # states won't be touched.
    restrictive_mode = False

    def __init__(self, raw):
        self.raw = raw
        self._stream = None
        # process special directives to init some special features
        self._process_special_events()

    def __repr__(self):
        return '<MarkupMachine(%s)>' % u', '.join(self.directives)

    def _process_special_events(self):
        # raw_directive
        self.raw_directive = rw = events.emit_ovr('define-raw-directive')(self)
        # and the raw directive name
        self.raw_name = rw.name

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
        stack = deque([''])
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
                            yield self.raw_name, text, self.raw_directive
                        del text_buffer[:]

                    if rule.enter is not None or rule.leave is not None:
                        enter, leave = rule.enter, rule.leave
                        if enter not in stack and rule.one:
                            # the rule is a standalone one so just yield
                            # the enter point and leave the context
                            token = leave and enter + self._begin or enter
                            yield token, m.group(), directive, True

                            # special case handling XXX: needs documentation
                            if leave:
                                # process special tokens before apply closing items.
                                if callable(rule.token):
                                    for item in rule.token(m):
                                        yield item
                                token = leave + self._end
                                yield token, m.group(), directive, False
                        elif leave is not None and leave in stack:
                            # there is some leaving-point defined so jump out
                            # of this context

                            # in restrictive mode we remove all tokens from the stack
                            # until we reach the token to leave.
                            if self.restrictive_mode:
                                while stack[0] != leave:
                                    yield stack[0], None, None, True
                                    stack.popleft()
                                stack.popleft()
                            else:
                                stack.remove(leave)
                            token = leave + self._end
                            yield token, m.group(), directive, True
                        elif enter is not None and not rule.one:
                            # enter a new context
                            stack.appendleft(enter)
                            token = enter + self._begin
                            yield token, m.group(), directive, False
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
                yield self.raw_name, text, self.raw_directive

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

        for callback in events.iter_callbacks('process-stream'):
            ret = callback(stream, ctx)
            if ret is not None:
                stream = ret

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
        if stream is None:
            stream = self.tokenize(enable_escaping=enable_escaping)

        # create the node-tree
        document = events.emit_ovr('define-document-node')()

        while not stream.eof:
            node = self.dispatch_node(stream)
            if node is not None:
                document.children.append(node)
            else:
                stream.next()

        # apply node-filters
        ctx = Context(self, enable_escaping)
        for callback in events.iter_callbacks('process-doc-tree'):
            ret = callback(document, ctx)
            if ret is not None:
                document = ret

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
