# simple-python-observable
A simple python implementation of the Observer design pattern.

This module provides an Observable data descriptor class, with register
and unregister attributes.

Assigning a value to the data descriptor object on instantiated enclosing
class objects will call all registered observer methods with the value as
the only passed argument.

Due to the nature of data descriptors, the register and unregister
attributes are inaccessible from instantiated enclosing class objects.
Thus, it is necessary to set the Observable's register and unregister
properties as properties of the enclosing class in the class definition.

The register method accepts either a callable (i.e. an unbound function),
or an instantiated object and the name of the method to call for updating.

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
    def notify(self, value):
        print "Observer.notify() called with {value!r}".format(value=value)

observer = Observer()

subject.thing_register(observer, 'notify')  # method name must be a string

subject.thing = 2  # Observer.notify will report receiving the value
print subject.thing  # Output will be the value from the preceding line

def observer_function(value):
    print "observer_function() called with {value!r}".format(value=value)

subject.thing_register(observer_function)

# Observer.notify and observer_function will report receiving the value
subject.thing = 3
print subject.thing  # Output will be the value from the preceding line

del observer

# observer_function will report receiving the value.  observer no longer
# exists, and will not be called.
subject.thing = 4
print subject.thing  # Output will be the value from the preceding line

subject.thing_unregister(observer_function)

subject.thing = 5  # No output will be produced
print subject.thing  # Output will be the value from the preceding line
```
