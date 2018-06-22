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

__all__ = ('Observable', 'Register', 'Unregister')


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
    def __set__(self, obj, value):
        self.observable.register(obj, value)

    def __call__(self, *args, **kwargs):
        return self.observable.register(self.obj, *args, **kwargs)


class Unregister(Registrar):  # pylint: disable=too-few-public-methods
    """ A Registrar non-data descriptor to gain access to the
        instantiated enclosing object and unregister the observer.
    """
    def __set__(self, obj, value):
        self.observable.unregister(obj, value)

    def __call__(self, *args, **kwargs):
        return self.observable.unregister(self.obj, *args, **kwargs)


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

    def get_value(self, obj):
        """ Retrieve the value for the obj instance """
        return self.value.get(obj, None)

    def __get__(self, obj, cls):
        return self if obj is None else self.get_value(obj)

    def __set__(self, obj, value):
        old_value = self.get_value(obj)
        self.value[obj] = value
        if self.notify or value != old_value:
            # notify the observers
            value = [value]
            if self.previous:
                value.append(old_value)
            for method in self.observer_methods(obj):
                method(*value)

    def observer_methods(self, obj):
        """ Yield a series of callable methods for the registered
            observers of the supplied obj
        """
        for (key, funcs) in self.get_observers_dict(obj).items():
            for func in funcs:
                if key is Observable:  # unbound functions/methods
                    yield func
                else:
                    yield func.__get__(key, type(key))

    def get_observers_dict(self, obj):
        """ Retrieve the dict of observers for the supplied obj """
        try:
            return self.observers[obj]
        except KeyError:
            observer_dict = self.observers[obj] = WeakKeyDictionary()
            return observer_dict

    def get_key_and_func(self, observer):
        """ Return the bound object and unbound method for the supplied
            observer

            Unbound methods and functions will return Observable, as
            None is not a valid value for a WeakKeyDictionary key.
        """
        # Bound methods will have a __self__ attribute.
        key = getattr(observer, '__self__', Observable)
        # Get the original unbound function.
        # This also neatly sidesteps the Python 2/3 variation.
        func = getattr(observer, '__func__', observer)
        return (key, func)

    def register(self, obj, observer):
        """ Register an observer """
        if not callable(observer):
            raise ValueError('observer is not callable')
        observer_dict = self.get_observers_dict(obj)
        (key, func) = self.get_key_and_func(observer)
        try:
            observer_dict[key].add(func)
        except KeyError:  # We need a new WeakKeyDictionary for obj
            observer_dict[key] = set([func])

    def unregister(self, obj, observer):
        """ Unregister an observer """
        observer_dict = self.get_observers_dict(obj)
        (key, func) = self.get_key_and_func(observer)
        try:
            key_observer = observer_dict[key]
        except KeyError:
            pass
        else:
            key_observer.discard(func)
            if not key_observer:  # Empty set?
                del observer_dict[key]
