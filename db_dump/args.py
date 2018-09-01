import argparse


class OptionAction(argparse.Action):
    def __init__(self, option_strings, dest, nargs=None, **kwargs):
        if nargs is not None:
            raise ValueError("nargs not allowed")
        super().__init__(option_strings, dest, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        sv = str(values)
        split = sv.split('=', 2)
        key = split[0].strip()
        val = split[1].strip()
        attr = getattr(namespace, self.dest)
        if not attr:
            setattr(namespace, self.dest, {})

        getattr(namespace, self.dest)[key] = val
