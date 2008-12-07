#!/usr/bin/env python
#-*- coding: utf-8 -*-
"""
    Advanced Example
    ----------------


    This example just implements some cool advanced
    markup thingies as tables, lists and other things
    like macros etc...

    This is a small mix out of MoinMoin, Inyoka-Markup and
    RestructedText (rest).
"""
from dmlt.machine import MarkupMachine, Directive, RawDirective, \
                         rule, bygroups
from dmlt.utils import parse_child_nodes
import nodes


class TextDirective(RawDirective):
    name = 'text'

    def parse(self, stream):
        return nodes.Text(stream.expect('text').value)


class SimpleMarkupDirective(Directive):
    __directive_node__ = None

    def parse(self, stream):
        dn = self.rule.enter
        begin, end = '%s_begin' % dn, '%s_end' % dn
        stream.expect(begin)
        children = parse_child_nodes(stream, self, end)
        stream.expect(end)
        return self.__directive_node__(children)


class EmphasizedDirective(SimpleMarkupDirective):
    __directive_node__ = nodes.Emphasized
    rule = rule(r"''", enter='emphasized', leave='emphasized')


class StrongDirective(SimpleMarkupDirective):
    __directive_node__ = nodes.Strong
    rule = rule(r'\*\*', enter='strong', leave='strong')


class UnderlineDirective(SimpleMarkupDirective):
    __directive_node__ = nodes.Underline
    rule = rule(r'__', enter='underline', leave='underline')


class SubscriptDirective(SimpleMarkupDirective):
    __directive_node__ = nodes.Sub
    rule = rule(r',,\(|\),,', enter='sub', leave='sub')


class SuperscriptDirective(SimpleMarkupDirective):
    __directive_node__ = nodes.Sup
    rule = rule(r'\^\^\(|\)\^\^', enter='sup', leave='sup')


class BigDirective(SimpleMarkupDirective):
    __directive_node__ = nodes.Big
    rule = rule(r'\+~\(|\)~\+', enter='big', leave='big')


class SmallDirective(SimpleMarkupDirective):
    __directive_node__ = nodes.Small
    rule = rule(r'-~\(|\)~-', enter='small', leave='small')


class AdvancedMarkupMachine(MarkupMachine):
    directives = [EmphasizedDirective, StrongDirective, UnderlineDirective,
                  SubscriptDirective, SuperscriptDirective, BigDirective,
                  SmallDirective]
    special_directives = [TextDirective]




TESTTEXT = u"""\
Some Cool Markup
================

This example's just adding some cool advanced text.

It is a mix out of MoinMoin, Inyoka-Markup and RestructedText (rest).
As you know is markup parsing a extremly hard thingy to implement. But as we
use DMLT – ''Descriptive Markup Language Toolkit'' – it's rather easy since it really
helps to outsource the parser implementation and just add the processing
methods as well as the regular-expressions to get DMLT some informations
on how to parse the raw text.

How it Works
------------

Just some \\''cool\\'' new paragraph.

escaped: \\\\\\
emphasized: ''text''
strong: **text**
underline: __underline__
subscript: ,,(subscript),,
superscript: ^^(Super!)^^
big: +~(big)~+
small: -~(small)~-
"""

def main():
    text = TESTTEXT
    print AdvancedMarkupMachine(text).render(enable_escaping=True)
