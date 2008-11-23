#-*- coding: utf-8 -*-
import re, os
from os.path import join
from dmlt import events
from dmlt.machine import MarkupMachine, Directive, RawDirective, \
    rule, bygroups
from dmlt.utils import escape, strip_ext, parse_child_nodes, filter_stream, \
    load_tree, dump_tree
import nodes


# Some terms the lexer understands as URL.
# Note that this list is far from complete...
_url_pattern = (
    # urls with netloc
    r'(?:(?:https?|ftps?|file|ssh|mms|svn(?:\+ssh)?|git|dict|nntp|irc|'
    r'rsync|smb)://|'
    # urls without netloc
    r'(?:mailto|telnet|s?news|sips?|skype):)'
)


class TextDirective(RawDirective):
    name = 'text'

    def parse(self, stream):
        return nodes.Text(stream.expect('text').value)

@events.register('define-raw-directive')
def _handle_register_raw_directive(mnager, *args, **kwargs):
    return TextDirective


class StrongDirective(Directive):
    rule = rule(r'\*\*', enter='strong')

    def parse(self, stream):
        stream.expect('strong_begin')
        children = parse_child_nodes(stream, self, 'strong_end')
        stream.expect('strong_end')
        return nodes.Strong(children)


class UnderlineDirective(Directive):
    rule = rule(r'__', enter='underline')

    def parse(self, stream):
        stream.expect('underline_begin')
        children = parse_child_nodes(stream, self, 'underline_end')
        stream.expect('underline_end')
        return nodes.Underline(children)


class EmphasizedDirective(Directive):
    rule = rule(r"''", enter='emphasized')

    def parse(self, stream):
        stream.expect('emphasized_begin')
        children = parse_child_nodes(stream, self, 'emphasized_end')
        stream.expect('emphasized_end')
        return nodes.Emphasized(children)


class EscapedCodeDirective(Directive):
    rule = rule(r'\`\`', enter='escaped_code')

    def parse(self, stream):
        stream.expect('escaped_code_begin')
        buffer = []
        while stream.current.type != 'escaped_code_end':
            buffer.append(stream.current.value)
            stream.next()
        stream.expect('escaped_code_end')
        return nodes.Code([nodes.Text(u''.join(buffer))])


class SubscriptDirective(Directive):
    rule = rule(r',,', enter='sub')

    def parse(self, stream):
        stream.expect('sub_begin')
        children = parse_child_nodes(stream, self, 'sub_end')
        stream.expect('sub_end')
        return nodes.Sub(children)


class SuperscriptDirective(Directive):
    rule = rule(r'\^\^\(|\)\^\^', enter='sup')

    def parse(self, stream):
        stream.expect('sup_begin')
        children = parse_child_nodes(stream, self, 'sup_end')
        stream.expect('sup_end')
        return nodes.Sup(children)


class StrokeDirective(Directive):
    rules = [
        rule(r'~~\(', enter='stroke_begin', one=True),
        rule(r'\)~~', enter='stroke_end', one=True)
    ]

    def parse(self, stream):
        if stream.test('stroke_end'):
            node = nodes.Text(stream.current.value)
            stream.next()
            return node
        stream.expect('stroke_begin')
        children = parse_child_nodes(stream, self, 'strike_end')
        stream.expect('stroke_end')
        return nodes.Stroke(children)


class BigDirective(Directive):
    rule = rule(r'\+~|~\+', enter='big')

    def parse(self, stream):
        stream.expect('big_begin')
        children = parse_child_nodes(stream, self, 'big_end')
        stream.expect('big_end')
        return nodes.Big(children)


class SmallDirective(Directive):
    rule = rule(r'-~|~-', enter='small')

    def parse(self, stream):
        stream.expect('small_begin')
        children = parse_child_nodes(stream, self, 'small_end')
        stream.expect('small_end')
        return nodes.Small(children)


class HeadlineDirective(Directive):
    rule = rule(r'(={1,6})(.*?)(\1)', bygroups('headline_level',
                'headline_text'), enter='headline', one=True)

    def parse(self, stream):
        stream.expect('headline')
        token = stream.expect('headline_level')
        return nodes.Headline(len(token.value.strip()),
            self.machine.parse(self.machine.tokenize(
            stream.expect('headline_text').value), True))


class LinkDirective(Directive):
    rule = rule(r'\[([^\s]+?\S)(\s(?:.+?))?\]', bygroups('link_href',
                'link_title'), enter='link', one=True)

    def parse(self, stream):
        stream.expect('link')
        return nodes.Link(stream.expect('link_href').value,
                          title=stream.expect('link_title').value)


class HTMLLinkDirective(Directive):
    rule = rule(_url_pattern+r'[^\s\'"]+\S', enter='html_link', one=True)

    def parse(self, stream):
        return nodes.Link(stream.expect('html_link').value)


class EmailDirective(Directive):
    rule = rule(r'[-\w._+]+\@[\w.-]+', enter='email', one=True)

    def parse(self, stream):
        return nodes.Link('mailto:%s' % stream.expect('email').value)


class CodeDirective(Directive):
    rules = [
        rule(r'\{\{\{', enter='code'),
        rule(r'\}\}\}', leave='code')
    ]

    def parse(self, stream):
        stream.expect('code_begin')
        data = escape(u''.join(filter_stream(stream, 'code_end')))
        stream.expect('code_end')
        return nodes.Preformatted([nodes.HTML(data)])


class RulerDirective(Directive):
    rule = rule(r'^----+\s*(\n|$)(?m)', enter='ruler', one=True)

    def parse(self, stream):
        stream.expect('ruler')
        return nodes.Ruler()


class SimpleMarkupMachine(MarkupMachine):

    directives = [EmailDirective, LinkDirective, HTMLLinkDirective,
                  StrongDirective, EmphasizedDirective, UnderlineDirective,
                  EscapedCodeDirective, BigDirective, SmallDirective,
                  SuperscriptDirective, SubscriptDirective, StrokeDirective,
                  HeadlineDirective, CodeDirective, RulerDirective]
    special_directives = [TextDirective]

def main():
    text=u'''
**bold __ underline __ ''italic'' **
+~upper~+

== Headline ==
==== Headline ====

[http://iamalink.xy alt text]

ftps://someinlinelink.xy

{{{
   that is a simple code block ``lala`` **daaaaaa!**
}}}

-------------
'''
    try:
        from pretty import pprint
    except ImportError:
        from pprint import pprint
    print "#######################################################"
    print "#############   TokenStream   #########################"
    stream = SimpleMarkupMachine(text).tokenize()
    print stream.debug()
    print
    print
    print
    print "########################################################"
    print "##############   Node Tree   ###########################"

    print SimpleMarkupMachine(text).parse()
    print
    print
    print
    print "########################################################"
    print "################# Rendered HTML ########################"
    print SimpleMarkupMachine(text).render()
    print
    print
    print
    print
    print "######################################################"
    print "##############  Compiled AST #########################"
    print dump_tree(SimpleMarkupMachine(text).parse(), 'html')
    print
    print
    print
    print
    print "######################################################"
    print "##############  loaded (compiled ) AST ###############"
    print load_tree(SimpleMarkupMachine(text).parse())
    print
    print
    print
    print
    print "######################################################"
    print "##############  loaded (not compiled) AST ############"
    print load_tree(dump_tree(SimpleMarkupMachine(text).parse(), 'html'))
