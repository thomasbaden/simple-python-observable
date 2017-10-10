"""An implementation of the Observer design pattern

    Usage:
        class Example(etc):
            thing = Observable()
            thing_register = thing.register
            thing_unregister = thing.unregister
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
from functools import partial
from weakref import WeakKeyDictionary


class Observable(object):
    """An implementation of the Observer design pattern
    """
    __slots__ = ('notify', 'observers', 'value')

    def __init__(self, always_notify=False):
        # These two WeakKeyDictionary objects use the instantiated
        # enclosing object as their key.  If the object goes away, so
        # does its item.
        self.observers = WeakKeyDictionary()
        self.value = WeakKeyDictionary()
        self.notify = always_notify

    def _get_value(self, obj):
        return self.value.get(obj, None)

    def __get__(self, obj, cls):
        if obj is None:
            # Referenced from an uninstantiated class definition. This
            # is how we access the register and unregister properties.
            return self
        return self._get_value(obj)

    def __set__(self, obj, value):
        old_value = self._get_value(obj)
        self.value[obj] = value
        if self.notify or value != old_value:
            # notify the observers
            for method in self._observer_methods(obj):
                method(value)

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

    def register_observer(self, obj, observer, method=None):
        """Register an observer.  If method is None, then the observer
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
        except KeyError:
            observerdict[obj] = WeakKeyDictionary({observer: method})

    def unregister_observer(self, obj, observer):
        """Unregister an observer.
        """
        self._get_observers(obj).pop(observer, None)

    class Registrar(object):  # pylint: disable=too-few-public-methods
        """Registrar abstract base class.  Only for subclassing and DRY.
        """
        __slots__ = ('observable', )
        def __init__(self, observable):
            self.observable = observable

    class Register(Registrar):  # pylint: disable=too-few-public-methods
        """A Registrar non-data descriptor to gain access to the
            instantiated enclosing object and register the observer.
        """
        def __get__(self, obj, _cls):
            if obj is None:
                return self
            return partial(self.observable.register_observer, obj)

    class Unregister(Registrar):  # pylint: disable=too-few-public-methods
        """A Registrar non-data descriptor to gain access to the
            instantiated enclosing object and unregister the observer.
        """
        def __get__(self, obj, _cls):
            if obj is None:
                return self
            return partial(self.observable.unregister_observer, obj)

    @property
    def register(self):
        """Return a Register non-data descriptor linked to this
            instantiated Observable.
        """
        return self.Register(self)

    @property
    def unregister(self):
        """Return a Unregister non-data descriptor linked to this
            instantiated Observable.
        """
        return self.Unregister(self)
