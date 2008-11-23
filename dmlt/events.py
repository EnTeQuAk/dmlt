#-*- coding: utf-8 -*-
"""
    dmlt.events
    ~~~~~~~~~~~

    Some kind of event handler used to hook up special
    things into the whole thing.

    :copyright: 2008 by Christopher Grebs.
    :license: BSD, see LICENSE for details.
"""
from dmlt.utils import patch_wrapper
from dmlt.errors import EventNotFound
from collections import deque


REGISTERED_EVENTS = [
    'define-raw-directive',
    'define-document-node',
    'process-stream',
    'process-doc-tree',
]


class EventManager(object):

    def __init__(self):
        self._store = {}

    def connect(self, event, callable):
        if not event in REGISTERED_EVENTS:
            raise EventNotFound(u'There is no event called %r' % event)

        if event not in self._store:
            self._store[event] = deque([callable])
        else:
            self._store[event].append(callable)

    def iter(self, event):
        if event not in self._store:
            return iter(())
        return iter(self._store[event])

    def remove(self, callable):
        for count, event in enumerate(self._store):
            if callable in event:
                event.remove(callable)
        return count

manager = EventManager()


def define(name):
    """
    This function can be used to extend the list of `REGISTERED_EVENTS`
    so that it's possible to hook in application defined events.
    """
    if name in REGISTERED_EVENTS:
        raise ValueError(u'event %r is already registered' % name)
    REGISTERED_EVENTS.append(name)


def register(name):
    """
    This function can be used as a decorator to register
    some callback object to an event.
    """
    def decorator(func):
        def proxy(*args, **kwargs):
            return func(manager, *args, **kwargs)
        proxy = patch_wrapper(proxy, func)
        manager.connect(name, proxy)
        return proxy
    return decorator


def emit(name, *args, **kwargs):
    return [cb(*args, **kwargs) for cb in manager.iter(name)] or None


def emit_ovr(name, *args, **kwargs):
    """
    a special `emit` method that returns only one (non-inheriting)
    value instead of a list.
    """
    value = None
    for callback in manager.iter(name):
        ret = callback(*args, **kwargs)
        if ret is not None:
            value = ret
    return value


def iter_callbacks(event):
    return manager.iter(event)
