#-*- coding: utf-8 -*-
from nose.tools import *
from dmlt.datastructure import Token


def test_token_repr():
    t = Token('foo', 'bar', end_of_context=True)
    assert_equal(t.as_tuple(), ('foo', 'bar', None, True))
    assert_equal(repr(t), r"<Token('foo', 'bar', None)>")
    assert_equal(unicode(t), u"<Token('foo', 'bar', None)>")


def test_token_cmp():
    t1 = Token('foo', 'bar', None, False)
    t2 = Token('bar', 'foo', None, True)
    t3 = Token('foo', 'bar', None, False)
    assert_false(t1 == t2)
    assert_true(t1 == t3)
    assert_false(t2 == t3)
    assert_true(t1 != t2)
    assert_raises(TypeError, lambda: t1 == 'foo')
