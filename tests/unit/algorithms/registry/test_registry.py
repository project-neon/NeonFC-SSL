import pytest
from neonfc_ssl.algorithms.registry import Registry


class FuncRegistry(Registry):
    marker = "_func_name"


def _fresh_registry() -> FuncRegistry:
    return FuncRegistry()


@pytest.mark.unit
def test_register_multiple_distinct_names():
    reg = _fresh_registry()

    @reg.register("a")
    def a():
        pass

    @reg.register("b")
    def b():
        pass

    assert reg.get("a") is a
    assert reg.get("b") is b


@pytest.mark.unit
def test_register_duplicate_raises_key_error():
    reg = _fresh_registry()

    @reg.register("dup")
    def first():
        pass

    with pytest.raises(KeyError):
        @reg.register("dup")
        def second():
            pass


@pytest.mark.unit
def test_missing_raises_key_error():
    reg = _fresh_registry()

    with pytest.raises(KeyError):
        reg.get("missing")


@pytest.mark.unit
def test_register_different_registries_are_independent():
    reg1 = _fresh_registry()
    reg2 = _fresh_registry()

    @reg1.register("x")
    def x():
        pass

    assert "x" in reg1
    assert "x" not in reg2


@pytest.mark.unit
def test_get_callable_is_invocable():
    reg = _fresh_registry()

    @reg.register("add")
    def add(a, b):
        return a + b

    assert reg.get("add")(2, 3) == 5


@pytest.mark.unit
def test_available_empty_registry():
    reg = _fresh_registry()
    assert reg.available() == []


@pytest.mark.unit
def test_available_lists_all_names():
    reg = _fresh_registry()

    for name in ("a", "b", "c"):
        reg.register(name)(lambda: None)

    assert set(reg.available()) == {"a", "b", "c"}


@pytest.mark.unit
def test_contains_true_for_registered_name():
    reg = _fresh_registry()

    @reg.register("present")
    def present():
        pass

    assert "present" in reg


@pytest.mark.unit
def test_contains_false_for_unknown_name():
    reg = _fresh_registry()
    assert "missing" not in reg


@pytest.mark.unit
def test_autodiscover_imports_modules_and_registers():
    from .resources import reg

    reg._entries.clear()

    reg.autodiscover("tests.unit.algorithms.registry.resources")
    assert reg.get("discoverable")(5) == 10
