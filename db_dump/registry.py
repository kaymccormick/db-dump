import sys
import threading

from zope.interface.registry import Components


def caller_module(level=2, sys=sys):
    module_globals = sys._getframe(level).f_globals
    module_name = module_globals.get('__name__') or '__main__'
    module = sys.modules[module_name]
    return module


def caller_package(level=2, caller_module=caller_module):
    # caller_module in arglist for tests
    module = caller_module(level + 1)
    f = getattr(module, '__file__', '')
    if (('__init__.py' in f) or ('__init__$py' in f)): # empty at >>>
        # Module is a package
        return module
    # Go up one level to get package
    package_name = module.__name__.rsplit('.', 1)[0]
    return sys.modules[package_name]


class _CALLER_PACKAGE(object):
    def __repr__(self): # pragma: no cover (for docs)
        return 'pyramid.path.CALLER_PACKAGE'

CALLER_PACKAGE = _CALLER_PACKAGE()

class Registry(Components):
    def __init__(self, package_name=CALLER_PACKAGE, *args, **kw):
        # add a registry-instance-specific lock, which is used when the lookup
        # cache is mutated
        self._lock = threading.Lock()
        if package_name is CALLER_PACKAGE:
            package_name = caller_package().__name__
        Components.__init__(self, package_name, *args, **kw)
