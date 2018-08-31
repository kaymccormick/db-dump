from zope.interface import implementer, Interface


class IFoo(Interface):
    def foo(self):
        pass
    pass

@implementer(IFoo)
class FooImpl:
    def foo(self):
        return 'foo'
    pass
