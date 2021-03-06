#-*- coding: utf-8 -*-
"""
    dmlt.exc
    ~~~~~~~~

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


class MissingContext(DMLTError, RuntimeError):
    """
    Cannot leave the parsing-context because
    we already leaved it or something undefined
    happened.
    """


class EventNotFound(DMLTError, RuntimeError):
    """
    This exception is raised if the event tried to register
    is not supported.
    """
