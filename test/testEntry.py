import unittest
from awsauditor.bill import Entry
from collections import OrderedDict


class EntryTest(unittest.TestCase):

    def testAddAppends(self):
        """
        Ensure that when a value is 'added' to the Entry, it goes to the very end.

        Add a new item to the Entry using .add(). Pop end value from the data in Entry and compare.
        """
        d = {'a': 1, 'b': 2, 'c': 3}
        o = OrderedDict(sorted(d.items(), key=lambda t: t[0]))
        e = Entry(o)
        new_item = ('test', 42)
        e.add(new_item[0], new_item[-1])
        self.assertEqual(new_item, e.data.popitem())