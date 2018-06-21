""" An implementation of the Observer design pattern

    Usage:
        class Example(etc):
            thing = Observable()
            thing_register = Register(thing)
            thing_unregister = Unregister(thing)
        sample = Example()
        sample.thing_register(function)
        sample.thing_register(someclass, 'foo')
        sample.thing = 1
        This results in calling function(1) and someclass.foo(1)
        One can't call sample.thing_register(someclass.foo), because
        the bound method someclass.foo is ephemeral and goes away
        immediately. Using the object separate from the method name
        defers binding the method until needed.

        The register and unregister @property methods return
        non-data descriptors, which is how we differentiate between
        separate instantiations of the enclosing class.
"""
from weakref import WeakKeyDictionary


class Registrar(object):  # pylint: disable=too-few-public-methods
    """ Registrar abstract base class.  Only for subclassing and DRY.
    """
    __slots__ = ('observable', 'obj')
    def __init__(self, observable, obj=None):
        self.observable = observable
        self.obj = obj

    def __get__(self, obj, _cls):
        return self if obj is None else type(self)(self.observable, obj)


class Register(Registrar):  # pylint: disable=too-few-public-methods
    """ A Registrar non-data descriptor to gain access to the
        instantiated enclosing object and register the observer.
    """
    def __call__(self, *args):
        return self.observable.register(self.obj, *args)


class Unregister(Registrar):  # pylint: disable=too-few-public-methods
    """ A Registrar non-data descriptor to gain access to the
        instantiated enclosing object and unregister the observer.
    """
    def __call__(self, *args):
        return self.observable.unregister(self.obj, *args)


class Observable(object):
    """ An implementation of the Observer design pattern

        Instantiate with always_notify=True to notify all observers on
        all set operations instead of set operations which change the
        value.

        Instantiate with include_previous=True to include the previous
        value in the notifications.
    """
    __slots__ = ('previous', 'notify', 'observers', 'value')

    def __init__(self, always_notify=False, include_previous=False):
        # These two WeakKeyDictionary objects use the instantiated
        # enclosing object as their key.  If the object goes away, so
        # does its item.
        self.observers = WeakKeyDictionary()
        self.value = WeakKeyDictionary()
        self.notify = always_notify
        self.previous = include_previous

    def _get_value(self, obj):
        return self.value.get(obj, None)

    def __get__(self, obj, cls):
        return self if obj is None else self._get_value(obj)

    def __set__(self, obj, value):
        old_value = self._get_value(obj)
        self.value[obj] = value
        if self.notify or value != old_value:
            # notify the observers
            value = [value]
            if self.previous:
                value.append(old_value)
            for method in self._observer_methods(obj):
                method(*value)

    @staticmethod
    def _observator(observer, method):
        return observer if method is None else getattr(observer, method)

    def _get_observers(self, obj):
        return self.observers.get(obj, {})

    def _observer_methods(self, obj):
        observers = self._get_observers(obj)
        _observator = self._observator
        return (_observator(observer, method)
                for observer, method in observers.items())

    def register(self, obj, observer, method=None):
        """ Register an observer.  If method is None, then the observer
            is a standalone function.  Otherwise, method is the name of
            a method to be found on the referenced observer object.
            This also means that there may only be one method per object
            that observes this value.
        """
        if not callable(self._observator(observer, method)):
            raise ValueError('observer is not callable')
        observerdict = self.observers
        try:
            observerdict[obj][observer] = method
        except KeyError:  # We need a new WeakKeyDictionary for obj
            observerdict[obj] = WeakKeyDictionary({observer: method})

    def unregister(self, obj, observer):
        """ Unregister an observer. """
        self._get_observers(obj).pop(observer, None)
