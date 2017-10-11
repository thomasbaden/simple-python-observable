# simple-python-observable
A simple python implementation of the Observer design pattern.

This module provides an `Observable` data descriptor class, with `register`
and `unregister` attributes.  This allows one to easily convert an object
attribute into an `Observable` without necessitating extensive changes to
one's program; just treat the `Observable` as though it were a normal
attribute.

The `Observable` may be instantiated with two optional arguments:
* `always_notify` (default=False)
* `include_previous` (default=False)

The `Observable`'s value starts out as `None`.  An initial value may, of
course, be set by the enclosing class's `__init__()` method.

When a value is assigned to the data descriptor object on instantiated
enclosing class objects, all registered observer methods will be called
if the value differs from the previous value, or if `always_notify` is true.
If `include_previous` is true, observers will be called with the previous
value as the second argument (e.g. `observer.method(new_value, old_value)`),
instead of just the new value (e.g. `observer.method(new_value)`).

Due to the nature of data descriptors, the `register` and `unregister`
attributes are inaccessible from instantiated enclosing class objects.
Thus, it is necessary to set the `Observable`'s `register` and `unregister`
properties as properties of the enclosing class in the class definition.

The register method accepts either a callable (i.e. an unbound function),
or an instantiated object and the name of the method to call for updating.
One cannot `register(someclass.foo)`, because the bound method `someclass.foo`
is ephemeral and goes away immediately.

Example usage:
```python
from observable import Observable

class Example(object):
    thing = Observable()
    thing_register = thing.register
    thing_unregister = thing.unregister

subject = Example()
subject.thing = 1  # No output will be produced
print subject.thing  # Output will be the value from the preceding line

class Observer(object):
    def __init__(self, name):
        self.name = name
    def notify(self, value):
        print "{name} Observer.notify() called with {value!r}".format(
            name=self.name, value=value)

observer = Observer('first')

subject.thing_register(observer, 'notify')  # method name must be a string

subject.thing = 2  # Observer.notify will report receiving the value
print subject.thing  # Output will be the value from the preceding line

def observer_function(value):
    print "observer_function() called with {value!r}".format(value=value)

subject.thing_register(observer_function)

# Observer.notify and observer_function will report receiving the value
subject.thing = 3
print subject.thing  # Output will be the value from the preceding line

observer2 = Observer('second')

subject.thing_register(observer2, 'notify')  # method name must be a string

# Observer.notify and observer_function will report receiving the value
subject.thing = 4
print subject.thing  # Output will be the value from the preceding line

subject.thing = 4  # Setting the same value will not notify the observers.
print subject.thing  # Output will be the value from the preceding line

del observer

# observer_function will report receiving the value.  observer no longer
# exists, and will not be called.  observer2 still exists, and will report
# receiving the value
subject.thing = 5
print subject.thing  # Output will be the value from the preceding line

subject.thing_unregister(observer2)
# observer_function will report receiving the value.  observer2 is not
# registered, and will not be notified
subject.thing = 6
print subject.thing  # Output will be the value from the preceding line

subject.thing_unregister(observer_function)

subject.thing = 7  # No output will be produced
print subject.thing  # Output will be the value from the preceding line
```
