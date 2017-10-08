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
    __slots__ = ('observers', 'value')

    def __init__(self):
        # These two WeakKeyDictionary objects use the instantiated
        # enclosing object as their key.  If the object goes away, so
        # does its item.
        self.observers = WeakKeyDictionary()
        self.value = WeakKeyDictionary()

    def __get__(self, obj, cls):
        if obj is None:
            # Referenced from an uninstantiated class definition. This
            # is how we access the register and unregister properties.
            return self
        return self.value.get(obj, None)

    def __set__(self, obj, value):
        self.value[obj] = value
        for method in self._observer_methods(obj):  # call the observers
            method(value)

    def _observer_methods(self, obj):
        observers = self.observers.get(obj, {})
        for observer, method in observers.items():
            yield observer if method is None else getattr(observer,
                                                          method)

    def register_observer(self, obj, observer, method=None):
        """Register an observer.  If method is None, then the observer
            is a standalone function.  Otherwise, method is the name of
            a method to be found on the referenced observer object.
            This also means that there may only be one method per object
            that observes this value.
        """
        if method is None:
            if not callable(observer):
                raise ValueError('observer is not callable')
        # Get the potential Attribute error at register time, not later.
        elif not callable(getattr(observer, method)):
            raise ValueError("observer's .{meth} method is not callable"
                             .format(meth=method))
        observerdict = self.observers
        try:
            observerdict[obj][observer] = method
        except KeyError:
            observerdict[obj] = WeakKeyDictionary({observer: method})

    def unregister_observer(self, obj, observer):
        """Unregister an observer.
        """
        try:
            self.observers[obj].pop(observer, None)
        except KeyError:
            pass

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
