"""Run the dependency's standard DATC assertions with unittest (no pytest needed)."""
import unittest
from diplomacy.tests.test_datc import TestDATC


class DATCTests(unittest.TestCase):
    pass


def wrap(name):
    def check(self):
        getattr(TestDATC(), name)()
    return check


for name in dir(TestDATC):
    if name.startswith('test_'):
        setattr(DATCTests, name, wrap(name))
