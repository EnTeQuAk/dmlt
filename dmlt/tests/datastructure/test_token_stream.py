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
from dmlt.datastructure import Token, TokenStream, _undefined, TokenStreamIterator


TEST_STREAM = [
    Token('bold', 'boldv'), Token('italic', 'italicv'), Token('uff', 'uffv'),
    Token('papapapa', 'papapapav'), Token('foo', 'foov'), Token('python', 'pythonv'),
    Token('spaghetti', 'spaghettiv'), Token('car', 'carv'), Token('mom', 'mom')
]
TEST_STREAM_TUPLE = list(t.as_tuple() for t in TEST_STREAM)


def test_feed():
    stream = TokenStream()
    for name in ('bold', 'italic', 'uff', 'papapapa', 'foo',
                 'python', 'spaghetti', 'car', 'mom'):
        stream.push(Token(name))
    for idx, received in enumerate(stream):
        exp = TEST_STREAM[idx]
        assert_equal(exp.type, received.type)
    stream.push(Token('fam', 'foo'), True)
    assert_equal(stream.current.type, 'fam')
    assert_true(stream.test('fam', 'foo'))
    assert_equal(Token('fam', 'foo'), stream.expect('fam', 'foo'))


def test_next():
    stream = TokenStream(iter(TEST_STREAM))
    for exp in TEST_STREAM:
        eq_(exp.as_tuple(), stream.current.as_tuple())
        stream.next()
    assert_equal(stream.current.type, 'eof')
    # test `TokenStream.eof` as well
    assert_true(stream.eof)


def test_look():
    stream = TokenStream.from_tuple_iter(TEST_STREAM)
    for iexp, exp in enumerate(TEST_STREAM):
        new = stream.look()
        if new.type != 'eof':
            assert_equal(TEST_STREAM[iexp+1].as_tuple(),
                         new.as_tuple())
        stream.next()
    # this is a bit fancy, but imho the right behaviour
    # XXX: does this belong here and not to `test_feed`?
    stream.push(Token('fooobaaaar'))
    assert_equal(stream.current.type, 'eof')
    assert_equal(stream.look().type, 'fooobaaaar')
    # skip the current 'eof' token and the 'fooobaaaar' token
    stream.skip(2)
    assert_equal(stream.current.type, 'eof')


def test_token_stream_iterator():
    #Low level tests, for more coverage
    stream = TokenStream.from_tuple_iter(TEST_STREAM_TUPLE)
    assert_true(isinstance(iter(stream), TokenStreamIterator))
    # check that TokenStreamIterator.__iter__ works as expected (required for coverage)
    assert_true(isinstance(iter(iter(stream)), TokenStreamIterator))
    iter_ = iter(stream)
    assert_equal(iter_._stream.current.type, 'bold')
    iter_.next()
    assert_equal(iter_._stream.current.type, 'italic')
