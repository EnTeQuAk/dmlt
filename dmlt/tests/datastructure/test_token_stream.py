#-*- coding: utf-8 -*-
"""
# initialize the stream
>>> stream = TokenStream.from_tuple_iter([1, 2, 3, 4, 5, 6])

# the current token in the stream
>>> stream.current
<Token(1, None, None)>

# look what's next in the stream
>>> stream.look()
<Token(2, None, None)>

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

# go one token ahead
>>> stream.next()
>>> stream.current
<Token(1, None, None)>

# push that 1 Token also away so that we can see if our token
# with value 7 is pushed right after Token(1).
>>> stream.next()
>>> stream.current
<Token(7, None, None)>

# assert the current token is from type `7` (see Token.type)
# and return the value. Note that `next` is called.
>>> stream.expect(7)
<Token(7, None, None)>

# `stream.expect` gone one token ahead.
>>> stream.current
<Token(2, None, None)>
"""
from nose.tools import *
from dmlt.datastructure import Token, TokenStream, _undefined


TEST_STREAM = [
    Token('bold'), Token('italic'), Token('uff'),
    Token('papapapa'), Token('foo'), Token('python'),
    Token('spaghetti'), Token('car'), Token('mom')
]
l = list


def test_feed():
    stream = TokenStream()
    for name in ('bold', 'italic', 'uff', 'papapapa', 'foo',
                 'python', 'spaghetti', 'car', 'mom'):
        stream.push(Token(name))
    for idx, received in enumerate(stream):
        exp = TEST_STREAM[idx]
        assert_equal(exp.type, received.type)


def test_next():
    stream = TokenStream(iter(TEST_STREAM))
    for exp in TEST_STREAM:
        eq_(exp.as_tuple(), stream.current.as_tuple())
        stream.next()
    assert_equal(stream.current.type, 'eof')


def test_look():
    stream = TokenStream(iter(TEST_STREAM))
    for iexp, exp in enumerate(TEST_STREAM):
        new = stream.look()
        if new.type != 'eof':
            assert_equal(TEST_STREAM[iexp+1].as_tuple(),
                         new.as_tuple())
        stream.next()
    assert_true(stream.look().type == 'eof')
