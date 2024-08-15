import abc
import collections.abc as cabc
import typing as t
import unittest

from wireflow.dependency import Dependency
from wireflow.dependency import DependencyInfo
from wireflow.dependency import DIContainer

T = t.TypeVar("T")


class TestInterface(abc.ABC):
    @abc.abstractmethod
    def do_something(self) -> str:
        pass


class TestImplementation(TestInterface):
    def do_something(self) -> str:
        return "something"


class DIContainerTests(unittest.IsolatedAsyncioTestCase):

    async def test_provide(self):
        class TestCase(t.Generic[T], t.TypedDict):
            name: str
            iface: type | None
            dep: T | None
            singleton: bool
            factory: cabc.Callable[[], T] | None
            dep_name: str
            want_err: bool

        tests: list[TestCase[t.Any]] = [
            {
                "name": "Provide valid dependency",
                "iface": TestInterface,
                "dep": TestImplementation(),
                "singleton": False,
                "factory": None,
                "dep_name": "",
                "want_err": False,
            },
            {
                "name": "Provide with nil dependency and factory",
                "iface": TestInterface,
                "dep": None,
                "singleton": False,
                "factory": None,
                "dep_name": "",
                "want_err": True,
            },
            {
                "name": "Provide with factory function",
                "iface": TestInterface,
                "dep": None,
                "singleton": True,
                "factory": lambda: TestImplementation(),
                "dep_name": "",
                "want_err": False,
            },
            {
                "name": "Provide with named dependency",
                "iface": TestInterface,
                "dep": TestImplementation(),
                "singleton": False,
                "factory": None,
                "dep_name": "TestImplementation1",
                "want_err": False,
            },
            {
                "name": "Provide with factory function that returns None",
                "iface": TestInterface,
                "dep": None,
                "singleton": True,
                "factory": lambda: None,
                "dep_name": "",
                "want_err": True,
            },
            {
                "name": "Provide with nil interface",
                "iface": None,
                "dep": TestImplementation(),
                "singleton": False,
                "factory": None,
                "dep_name": "",
                "want_err": False,
            },
            {
                "name": "Provide without dependency nor interface",
                "iface": None,
                "dep": None,
                "singleton": False,
                "factory": None,
                "dep_name": "",
                "want_err": True,
            },
            {
                "name": "Provide with invalid interface",
                "iface": str,  # Invalid, as it's not an interface.
                "dep": TestImplementation(),
                "singleton": False,
                "factory": None,
                "dep_name": "",
                "want_err": True,
            },
            {
                "name": "Provided dependency does not implement interface",
                "iface": TestInterface,
                "dep": "invalid",  # Invalid, does not implement TestInterface
                "singleton": False,
                "factory": None,
                "dep_name": "",
                "want_err": True,
            },
            {
                "name": "Provide with invalid name",
                "iface": TestInterface,
                "dep": TestImplementation(),
                "singleton": False,
                "factory": None,
                "dep_name": "-1",  # Invalid name
                "want_err": True,
            },
        ]

        for tt in tests:
            with self.subTest(tt["name"]):
                c = DIContainer()
                if tt["want_err"]:
                    with self.assertRaises(ValueError):
                        await c.provide(
                            tt["dep"],
                            tt["singleton"],
                            tt["iface"],
                            tt["factory"],
                            tt["dep_name"],
                        )
                else:
                    await c.provide(
                        tt["dep"],
                        tt["singleton"],
                        tt["iface"],
                        tt["factory"],
                        tt["dep_name"],
                    )
                    if tt["iface"]:
                        deps = c._dependencies.get(tt["iface"], [])  # type: ignore
                        self.assertTrue(deps, "Dependency was not stored")
                    if tt["dep_name"]:
                        self.assertIn(
                            tt["dep_name"],
                            c._registry,  # type: ignore
                            "Dependency name was not stored",
                        )

    async def test_resolve(self):
        class TestCase(t.Generic[T], t.TypedDict):
            name: str
            iface: type | None
            dep: T | None
            singleton: bool
            factory: cabc.Callable[[], T] | None
            dep_name: str
            want_err: bool

        tests: list[TestCase[t.Any]] = [
            {
                "name": "Resolve existing dependency by type name",
                "iface": TestInterface,
                "dep": TestImplementation(),
                "singleton": False,
                "factory": None,
                "dep_name": "",
                "want_err": False,
            },
            {
                "name": "Resolve existing named dependency",
                "iface": TestInterface,
                "dep": TestImplementation(),
                "singleton": False,
                "factory": None,
                "dep_name": "TestImplementation1",
                "want_err": False,
            },
            {
                "name": "Resolve non-existing dependency",
                "iface": TestInterface,
                "dep": None,
                "singleton": False,
                "factory": None,
                "dep_name": "",
                "want_err": True,
            },
            {
                "name": "Resolve singleton dependency with factory",
                "iface": TestInterface,
                "dep": None,
                "singleton": True,
                "factory": lambda: TestImplementation(),
                "dep_name": "",
                "want_err": False,
            },
            {
                "name": "Resolve singleton dependency without factory",
                "iface": TestInterface,
                "dep": TestImplementation(),
                "singleton": True,
                "factory": None,
                "dep_name": "",
                "want_err": False,
            },
            {
                "name": "Resolve first dependency with empty name",
                "iface": TestInterface,
                "dep": TestImplementation(),
                "singleton": False,
                "factory": None,
                "dep_name": "",
                "want_err": False,
            },
            {
                "name": "Resolve last dependency with '-1' name",
                "iface": TestInterface,
                "dep": TestImplementation(),
                "singleton": False,
                "factory": None,
                "dep_name": "-1",
                "want_err": False,
            },
            {
                "name": "Resolve with invalid name",
                "iface": TestInterface,
                "dep": TestImplementation(),
                "singleton": False,
                "factory": None,
                "dep_name": "nonexistent",
                "want_err": True,
            },
            {
                "name": "Resolve non-singleton dependency with factory function",
                "iface": TestInterface,
                "dep": None,
                "singleton": False,
                "factory": lambda: TestImplementation(),
                "dep_name": "",
                "want_err": False,
            },
            {
                "name": "Resolve with invalid type",
                "iface": None,
                "dep": None,
                "singleton": False,
                "factory": None,
                "dep_name": "",
                "want_err": True,
            },
            {
                "name": "Resolve with type mismatch between given type and dependency name",
                "iface": TestInterface,
                "dep": TestImplementation(),
                "singleton": False,
                "factory": None,
                "dep_name": "mismatch",
                "want_err": True,
            },
        ]

        for tt in tests:
            with self.subTest(tt["name"]):
                c = DIContainer()
                if tt["dep_name"] == "mismatch":
                    c._dependencies[tt["iface"]] = [Dependency(tt["dep"], tt["factory"], tt["singleton"])]  # type: ignore
                    c._registry[tt["dep_name"]] = DependencyInfo(interface=str, implementation=TestImplementation)  # type: ignore
                elif tt["dep"] is not None or tt["factory"] is not None:
                    await c.provide(
                        tt["dep"],
                        tt["singleton"],
                        tt["iface"],
                        tt["factory"],
                        tt["dep_name"],
                    )

                if tt["want_err"]:
                    with self.assertRaises(KeyError):
                        await c.resolve(tt["iface"], tt["dep_name"])  # type: ignore
                else:
                    val = t.cast(object, await c.resolve(tt["iface"], tt["dep_name"]))  # type: ignore
                    self.assertIsInstance(val, TestInterface)
                    self.assertEqual(t.cast(TestInterface, val).do_something(), "something")

    async def test_resolve_all(self):
        class TestCase(t.Generic[T], t.TypedDict):
            name: str
            iface: type | None
            deps: list[T]
            want_err: bool

        tests: list[TestCase[t.Any]] = [
            {
                "name": "ResolveAll with multiple dependencies",
                "iface": TestInterface,
                "deps": [TestImplementation(), TestImplementation()],
                "want_err": False,
            },
            {
                "name": "ResolveAll with no dependencies",
                "iface": TestInterface,
                "deps": [],
                "want_err": True,
            },
            {
                "name": "ResolveAll with invalid type",
                "iface": None,
                "deps": [],
                "want_err": True,
            },
            {
                "name": "ResolveAll with invalid dependency",
                "iface": TestInterface,
                "deps": [None],
                "want_err": True,
            },
        ]

        for tt in tests:
            with self.subTest(tt["name"]):
                c = DIContainer()
                for dep in tt["deps"]:
                    if dep is not None:
                        await c.provide(dep, False, None, tt["iface"], None)
                    else:
                        c._dependencies[tt["iface"]] = []  # type: ignore

                if tt["want_err"]:
                    with self.assertRaises(KeyError):
                        await c.resolve_all(tt["iface"])  # type: ignore
                else:
                    results: list[object] = await c.resolve_all(tt["iface"])  # type: ignore
                    self.assertEqual(len(results), len(tt["deps"]))
                    for dep in results:
                        self.assertIsInstance(dep, TestInterface)
                        self.assertEqual(t.cast(TestInterface, dep).do_something(), "something")

    async def test_delete(self):
        class TestCase(t.TypedDict):
            name: str
            iface: type
            dep: TestImplementation | None
            want_exist: bool

        tests: list[TestCase] = [
            {
                "name": "Delete existing dependency",
                "iface": TestInterface,
                "dep": TestImplementation(),
                "want_exist": False,
            },
            {
                "name": "Delete non-existing dependency",
                "iface": TestInterface,
                "dep": None,
                "want_exist": False,
            },
        ]

        for tt in tests:
            with self.subTest(tt["name"]):
                c = DIContainer()
                if tt["dep"]:
                    await c.provide(tt["dep"], False, None, tt["iface"], None)

                await c.delete(tt["iface"])

                if tt["want_exist"]:
                    val = t.cast(object, await c.resolve(tt["iface"], None))
                    self.assertIsNotNone(val)
                else:
                    with self.assertRaises(KeyError):
                        await c.resolve(tt["iface"], None)


if __name__ == "__main__":
    unittest.main()
