#-*- coding: utf-8 -*-
"""
    dmlt.errors
    ~~~~~~~~~~~

    Some builtin exceptions.

    :copyright: 2007-2008 by Christopher Grebs.
    :license: BSD, see LICENSE for more details.
"""


class DMLTError(Exception):
    """
    Base Exception class for all
    errors raised in DMLT.
    """
    def __init__(self, msg=''):
        self.msg = msg
        Exception.__init__(self, msg)

    def __str__(self):
        return self.msg


class StackEmpty(DMLTError, RuntimeError):
    """
    Raised if the user tries to modify
    non-existing items in the stack
    """

class HandlerNotFound(DMLTError, KeyError):
    """
    Raised if no markup handler was found,
    but a regex defines one.
    """

class HandlerError(DMLTError, RuntimeError):
    """
    Maybe something was misconfigured
    due handling some ``handlers``.
    """
