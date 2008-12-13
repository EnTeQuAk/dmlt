#-*- coding: utf-8 -*-

from nose.tools import *
from dmlt.exc import StackEmpty
from dmlt.datastructure import Stack, Token, _undefined


TEST_TOKENS = ['bold', 'italic', 'uff', 'papapapa', 'foo', 'python',
    'spaghetti', 'car', 'mom']


def test_current():
    stack = Stack()
    assert_true(stack.current is _undefined)
    stack.push('foo')
    assert_equal(stack.current, 'foo')
    stack.pop()
    assert_true(stack.current is _undefined)
    stack.push('foo, part 2')
    stack.flush()
    assert_true(stack.current is _undefined)
    stack = Stack(['foo', 'bar', 'baz'])
    assert_equal(stack.current, 'baz')


def test_lookup():
    stack = Stack(['foo', 'bar', 'fooz', 'baz'])
    assert_equal(list(stack.lookup()), ['foo', 'bar', 'fooz', 'baz'])


def test_pop():
    stack = Stack(['foo'])
    assert_equal(stack.current, 'foo')
    assert_equal(stack.pop(), 'foo')
    assert_equal(stack.current, _undefined)
    assert_raises(StackEmpty, stack.pop)


def test_push():
    stack = Stack()
    stack.push('foo')
    stack.push('baar')
    assert_equal(stack.current, 'baar')
    stack.push('baz')
    assert_equal(list(stack.lookup()), ['foo', 'baar', 'baz'])


def test_flush():
    stack = Stack(['foo', 'bar'])
    flushed = stack.flush()
    assert_true(isinstance(flushed, Stack))
    assert_equal(list(flushed), ['foo', 'bar'])


def test_complete_stack():
    l = list
    stack = Stack()
    assert_true(stack.current is _undefined)
    for i, token in enumerate(TEST_TOKENS):
        stack.push(token)
        assert_true(isinstance(token, str))
        assert_equal(stack.current, token)
    for expected, received in zip(TEST_TOKENS, stack.flush()):
        assert_equal(expected, received)
    assert_equal(l(stack._stack), [])
