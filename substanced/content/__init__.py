import inspect

from zope.interface import (
    alsoProvides,
    Interface,
    implementer,
    )

import venusian

from ..interfaces import (
    IContent,
    ICatalogable,
    IPropertied,
    )

_marker = object()

Type = Interface # API

def addbase(iface1, iface2):
    if not iface2 in iface1.__iro__:
        iface1.__bases__ += (iface2,)
        return True
    return False

def get_content_types(context):
    return getattr(context, '__content_types__', ())

def set_content_type(factory, type):
    content_types = getattr(factory, '__content_types__', ())
    if not type in content_types:
        content_types = tuple(content_types) + (type,)
    factory.__content_types__ = content_types

class ContentRegistry(object):
    def __init__(self):
        self.factories = {}
        self.meta = {}

    def add(self, content_type, factory, **meta):
        self.factories[content_type] = factory
        self.meta[content_type] = meta
        
    def create(self, content_type, *arg, **kw):
        return self.factories[content_type](*arg, **kw)

    def all(self, context=_marker, **meta):
        if context is _marker:
            candidates = self.factories.keys()
        else:
            candidates = [
                t for t in get_content_types(context) if t in self.factories]

        if not meta:
            return candidates
        
        matches_meta = []

        for candidate in candidates:
            ok = True
            for k, v in meta.items():
                if not self.meta.get(candidate, {}).get(k) == v:
                    ok = False
                    break
            if ok:
                matches_meta.append(candidate)
                
        return matches_meta

    def first(self, context, **meta):
        matching = self.all(context, **meta)
        if not matching:
            raise ValueError('No match!')
        return matching[0]

    def metadata(self, context, name, default=None):
        content_types = self.all(context)
        for typ in content_types:
            maybe = self.meta.get(typ, {}).get(name, default)
            if maybe is not None:
                return maybe
        return default

    def istype(self, context, type):
        return type in getattr(context, '__content_types__', [])

# venusian decorator that marks a class as a content class
class content(object):
    """ Use as a decorator for a content factory (usually a class).  Accepts
    a content interface and a set of meta keywords."""
    venusian = venusian
    def __init__(self, content_type, **meta):
        self.content_type = content_type
        self.meta = meta

    def __call__(self, wrapped):
        def callback(context, name, ob):
            config = context.config.with_package(info.module)
            config.add_content_type(self.content_type, wrapped, **self.meta)
        info = self.venusian.attach(wrapped, callback, category='substanced')
        self.meta['_info'] = info.codeinfo # fbo "action_method"
        return wrapped
    
def add_content_type(config, content_type, factory, **meta):
    """
    Configurator method which adds a content type.  Call via
    ``config.add_content_type`` during Pyramid configuration phase.
    ``content_type`` is a hashable object (usually a string) representing the
    content type.  ``factory`` is a class or function which produces a
    content instance.  ``**meta`` is an arbitrary set of keywords associated
    with the content type in the content registry.

    Some of the keywords in ``**meta`` have special meaning:

    - If ``meta`` contains the keyword ``propertysheets``, the content type
      will obtain a tab in the SDI that allows users to manage its
      properties.

    - If ``meta`` contains the keyword ``catalog`` and its value is true, the
      object will be tracked in the Substance D catalog.

    Other keywords will just be stored, and have no special meaning.
    """
    interfaces = meta.get('interfaces', [])

    if not IContent in interfaces:
        interfaces.append(IContent)

    if meta.get('catalog'):
        if not ICatalogable in interfaces:
            interfaces.append(ICatalogable)

    if meta.get('propertysheets') is not None:
        if not IPropertied in interfaces:
            interfaces.append(IPropertied)

    if inspect.isclass(factory):
        implementer(interfaces)(factory)
        set_content_type(factory, content_type)
        
    else:
        factory = provides_factory(factory, content_type, interfaces)
    
    def register_factory():
        config.registry.content.add(content_type, factory, **meta)

    discrim = ('sd-content-type', content_type)
    
    intr = config.introspectable(
        'substance d content types',
        discrim, content_type,
        'substance d content type',
        )
    intr['meta'] = meta
    intr['content_type'] = content_type
    intr['interfaces'] = tuple(interfaces)
    intr['factory'] = factory
    config.action(discrim, callable=register_factory, introspectables=(intr,))

def provides_factory(factory, content_type, interfaces):
    """ Wrap a function factory in something that applies the provides
    interfaces to the created object as necessary"""
    def add_provides(*arg, **kw):
        inst = factory(*arg, **kw)
        for interface in interfaces:
            if not interface.providedBy(inst):
                alsoProvides(inst, interface)
        set_content_type(inst, content_type)
        return inst
    for attr in ('__doc__', '__name__', '__module__'):
        if hasattr(factory, attr):
            setattr(add_provides, attr, getattr(factory, attr))
    add_provides.__orig__ = factory
    return add_provides

def includeme(config): # pragma: no cover
    config.registry.content = ContentRegistry()
    config.add_directive('add_content_type', add_content_type)

# usage:
# registry.content.create(IFoo, 'a', bar=2)
# registry.content.all(context)
# registry.content.all()
# registry.content.first(context)
# registry.content.metadata(**match)
