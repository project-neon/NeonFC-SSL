from .transformation_registry import transformation_registry

get = transformation_registry.get
available = transformation_registry.available

transformation_registry.autodiscover(__name__)
