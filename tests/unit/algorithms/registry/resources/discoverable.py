from . import reg


@reg.register("discoverable")
def discoverable(x):
    return x * 2
