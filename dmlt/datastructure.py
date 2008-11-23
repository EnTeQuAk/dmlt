#-*- coding: utf-8 -*-
"""
    dmlt.datastructure
    ~~~~~~~~~~~~~~~~~~

    Serveral helpers for token processing including
    a TokenStream as well as a Stack.

    :copyright: 2006-2008 by Christopher Grebs
    :license: BSD, see LICENSE for more details.
"""
import sys
from copy import copy as ccopy
from dmlt.errors import StackEmpty


__all__ = ('Token', 'TokenStream', 'Stack', 'Context')


_undefined = object()


class Token(object):
    """
    A token prepresents a part of a document with
    references to a directive that processes that
    token.
    """

    __slots__ = ('type', 'value', 'directive', 'end_of_context')

    def __init__(self, type, value=None, directive=None, end_of_context=False):
        self.type = type
        self.value = value
        self.directive = directive
        self.end_of_context = end_of_context

    def as_tuple(self):
        return (self.type, self.value, self.directive)

    def __repr__(self):
        return '<Token(%r, %r, %r)>' % self.as_tuple()
    __str__ = __repr__

    def __unicode__(self):
        return unicode(self.__str__())

    def __cmp__(self, other):
        if not isinstance(other, self.__class__):
            raise TypeError('Can\'t compare %s with %s'
                % (repr(other), repr(self.__class__)))
        return other.as_tuple() == self.as_tuple()


class TokenStreamIterator(object):
    """Iteration interface for the TokenStream"""

    def __init__(self, stream):
        self._stream = stream

    def __iter__(self):
        return self

    def next(self):
        token = self._stream.current
        if token.type == 'eof':
            raise StopIteration
        self._stream.next()
        return token


class TokenStream(object):
    """
    A token stream wraps a generator and supports pushing tokens back
    to the stream. It also provides some functions to expect tokens
    and similar stuff.

    There are two ways to initialize a TokenStream. One uses a generator
    that yields `Token` instances and the other can be used to inizialize
    the TokenStream with any object::

        # initialize the stream with a generator that yields `Token` instances
        >>> stream = TokenStream((Token(x) for x in xrange(1, 7)))
        # or initialize the stream from an iterable of numbers
        >>> stream = TokenStream.from_tuple_iter([1, 2, 3, 4, 5, 6])

    To see what's going on in the stream, there are `current` and the `look`
    method::

        # the current token in the stream
        >>> stream.current
        <Token(1, None, None)>
        # look what's next in the stream
        >>> stream.look()
        <Token(2, None, None)>

    Well this stream works most as a generator object does. But except
    that it allows to push tokens back to the stream. See the examples::

        # push one token back to the stream right after the current one
        >>> stream.push(Token(7))
        # the current token was not touched. To do so use `stream.shift`
        # (see below)
        >>> stream.current
        <Token(1, None, None)>

        # push a new token to the stream right *before* the current
        # token so that the current token is the pushed one.
        >>> stream.shift(Token(20))
        >>> stream.current
        <Token(20, None, None)>

    As you see it's easy to manipulate the token stream. But note, never
    push more then one token back to the stream. Although the stream object
    won't stop you that behaviour is undefined!
    Well, a TokenStream supports as a generator object does some methods to
    walk through the stream. That's in fact the `next` and `expect` methods.

    ::

        # go one token ahead
        >>> stream.next()
        >>> stream.current
        <Token(1, None, None)>

        # assert the current token is from type `7` (see Token.type)
        # and return the value. Note that `next` is called.
        >>> stream.expect(7)
        <Token(7, None, None)>
        >>> stream.current      # `stream.expect` gone one token ahead.
        <Token(2, None, None)>

    Additional features: `test`, `skip`.
    """

    def __init__(self, generator=None):
        generator = generator or iter([])
        self._next = generator.next
        self._pushed = []
        self.current = Token('initial', _undefined, _undefined)
        self.next()

    @classmethod
    def from_tuple_iter(cls, iterable=None):
        """
        Initialize the stream with an `iterable`. If the iterable-children
        are no `Token` instances they're wrapped into a `Token` one.
        """
        _iter = []
        iterable = iterable or []
        for item in iterable:
            if hasattr(item, 'as_tuple'):
                _iter.append(item.as_tuple())
            elif isinstance(item, (tuple, set, frozenset, list)):
                _iter.append(item)
            else:
                _iter.append((item,))
        return cls(Token(*a) for a in _iter)

    def __iter__(self):
        return TokenStreamIterator(self)

    @property
    def eof(self):
        """Are we at the end of the tokenstream?"""
        return not bool(self._pushed) and self.current.type == 'eof'

    def debug(self, stream=None):
        """Displays the tokenized code on the stream provided or stdout."""
        if stream is None:
            stream = sys.stdout
        for token in self:
            stream.write(repr(token) + '\n')

    def look(self):
        """See what's the next token."""
        if self._pushed:
            return self._pushed[-1]
        old_token = self.current
        self.next()
        new_token = self.current
        self.current = old_token
        self.push(new_token)
        return new_token

    def push(self, token, current=False):
        """Push a token back to the stream (only one!)."""
        self._pushed.append(token)
        if current:
            self.next()

    def skip(self, n):
        """Go n tokens ahead."""
        for idx in xrange(n):
            self.next()

    def next(self):
        """Go one token ahead."""
        if self._pushed:
            self.current = self._pushed.pop()
        else:
            try:
                self.current = self._next()
            except StopIteration:
                if self.current.type != 'eof':
                    self.current = Token('eof')

    def expect(self, type, value=None):
        """expect a given token."""
        assert self.current.type == type
        if value is not None:
            assert self.current.value == value or \
                   (value.__class__ is tuple and
                    self.current.value in value)
        try:
            return self.current
        finally:
            self.next()

    def test(self, type, value=Ellipsis):
        """Test the current token."""
        return self.current.type == type and \
               (value is Ellipsis or self.current.value == value or
                value.__class__ is tuple and \
                self.current.value in value)

    def shift(self, token):
        """
        Push one token into the stream.
        """
        old_current = self.current
        self.next()
        self.push(self.current)
        self.push(old_current)
        self.push(token)
        self.next()


class Context(dict):
    """
    An object that works (mostly) like a dictionary but
    supports some new features like *callbacks* for the
    `update` method.

    It's used for the `MarkupMachine` to store special
    environment variables as well as for node and stream filters
    to set some special environment variables in the context
    and to have a reference to the current `MarkupMachine` instance.

    :param machine: The current `MarkupMachine` instance.
    """
    def __init__(self, machine, escaping_enabled=False):
        self.machine = machine
        self.escaping_enabled = escaping_enabled
        dict.__init__(self)

    def update(self, key, value=None, callback=None):
        """
        Return the value of the ``key`` or if applied
        the return value of ``callback``.
        """
        if value is None and callback is None:
            raise TypeError('ParserContext.update takes at least'
                            ' three arguments (2 given)')
        elif not callback is None and callable(callback):
            value = callback(self.get(key))
        elif not key in self:
            raise ValueError('key %r does not exist' % key)
        self[key] = value
        return value

    def __repr__(self):
        return '%s(%r, %r)' % (
            self.__class__.__name__,
            self.machine
        )


class Stack(object):
    """
    The `Stack` implements a simple LIFO stack that
    is used by the `Machine`.

    To push new data into the stack use `push(item)`.
    *item* can be any object. The stack doesn't matter
    of the objects it handles.

        >>> stack.push('foo')
        >>> stack.push(Token('bar', 'baz'))
        >>> stack.push(123456)

    To view the current token use the `current` property::

        >>> stack.current
        123456

    To get a new `Stack` instance without any reference to the current one
    use `lookup`.
    The same way as list objects does you can `pop` the last item from
    the stack. It's returned. If the stack is empty `StackEmpty` is raised.

    `flush` returns the current stack object as the `lookup` method does
    but deletes the stack afterwards.
    """

    def __init__(self, iterable=None):
        if iterable is not None:
            self._stack = list(iterable)
        else:
            self._stack = []

    @property
    def current(self):
        if self._stack:
            return self._stack[-1]
        else:
            return _undefined

    def lookup(self):
        """
        Return the stack without touch the stack itself.
        That way you can use it to lookup the current stack.
        """
        return Stack(ccopy(self._stack))

    def pop(self):
        """
        Delete the last token in the stack and return it.
        A `StackEmpty` exception is thrown if the stack is empty.
        """
        if not self._stack:
            raise StackEmpty()
        return self._stack.pop()

    def push(self, item):
        """
        Append an item to the stack.
        """
        self._stack.append(item)

    def flush(self):
        """Return the whole stack and delete it afterwards"""
        old = ccopy(self._stack)
        del self._stack[:]
        return Stack(old)

    def __iter__(self):
        return iter(self._stack)

    def __repr__(self):
        return '<%s (%s)>' % (
            self.__class__.__name__,
            self._stack or 'empty'
        )
