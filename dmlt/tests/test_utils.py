#-*- coding: utf-8 -*-

from nose.tools import *
from dmlt.utils import lstrip_ext, rstrip_ext, strip_ext, escape, unescape, \
    replace_entities, striptags


def test_lstrip():
    assert_equal(lstrip_ext(' d i lllaaaadddiii', 'di '), 'lllaaaadddiii', 2)
    assert_equal(lstrip_ext('  dd laladidid', 'd ', 3), 'd laladidid', 2)


def test_rstrip():
    assert_equal(rstrip_ext('llaaddd d i   ', 'di '), 'llaa', 2)
    assert_equal(rstrip_ext('llaaddd d i   ', 'di ', 4), 'llaaddd d ', 2)


def test_strip():
    assert_equal(strip_ext('   lala   '), 'lala')
    assert_equal(strip_ext('   lalala   ', num=2), ' lalala ')


def test_escape():
    assert_equal(escape('you & me are so < then >'),
                        'you &amp; me are so &lt; then &gt;')
    assert_equal(escape('I love "foo" >> bar!', True),
                        'I love &quot;foo&quot; &gt;&gt; bar!')


def test_unescape():
    assert_equal(unescape('you &amp; me are so &lt; then &gt;'),
                          'you & me are so < then >')
    assert_equal(unescape('I love &quot;foo&quot; &gt;&gt; bar!&copy;'),
                          u'I love "foo" >> bar!©')


def test_replace_entities():
    assert_equal(replace_entities('foo &amp; bar &raquo; foo'), u'foo & bar \xbb foo')


def test_striptags():
    assert_equal(striptags('foo <b>bar</b> foo<ins>baaaar</ins>'), u'foo bar foobaaaar')
