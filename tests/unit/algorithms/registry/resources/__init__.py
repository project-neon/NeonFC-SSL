from neonfc_ssl.algorithms.registry import Registry


class FuncRegistry(Registry):
    marker = "_func_name"


reg = FuncRegistry()
