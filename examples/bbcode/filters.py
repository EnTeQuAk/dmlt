#-*- coding: utf-8 -*-
import re
from dmlt import events
import nodes


_newline_re = re.compile(r'(\n)')
_paragraph_re = re.compile(r'(\s*?\n){2,}')


def joined_text_iter(node):
    """
    This function joins multiple text nodes that follow each other into
    one.
    """
    text_buf = []

    def flush_text_buf():
        if text_buf:
            text = u''.join(text_buf)
            if text:
                yield nodes.Text(text)
            del text_buf[:]

    for child in node.children:
        if child.is_text_node:
            text_buf.append(child.text)
        else:
            for item in flush_text_buf():
                yield item
            yield child
    for item in flush_text_buf():
        yield item


@events.register('process-doc-tree')
def process(emanager, parent, ctx):
    """
    Insert real paragraphs into the node and return it.
    """
    for node in parent.children:
        if node.is_container and not node.is_raw:
            process(node, ctx)

    if not parent.allows_paragraphs:
        return parent

    paragraphs = [[]]

    for child in joined_text_iter(parent):
        if child.is_text_node:
            blockiter = iter(_paragraph_re.split(child.text))
            for block in blockiter:
                try:
                    is_paragraph = blockiter.next()
                except StopIteration:
                    is_paragraph = False
                if block:
                    paragraphs[-1].append(nodes.Text(block))
                if is_paragraph:
                    paragraphs.append([])
        elif child.is_block_tag:
            paragraphs.extend((child, []))
        else:
            paragraphs[-1].append(child)

    del parent.children[:]
    for paragraph in paragraphs:
        if not isinstance(paragraph, list):
            parent.children.append(paragraph)
        else:
            for node in paragraph:
                if not node.is_text_node or node.text:
                    parent.children.append(nodes.Paragraph(paragraph))
                    break

    return parent
