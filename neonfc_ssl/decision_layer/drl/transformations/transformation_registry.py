from typing import Callable
from neonfc_ssl.algorithms.registry import Registry


class TransformationRegistry(Registry[Callable]):
    marker = "transformation_name"


transformation_registry = TransformationRegistry()
