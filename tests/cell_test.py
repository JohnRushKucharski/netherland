'''
Unit tests for cell.py module.
'''
import unittest

from src.cell import enumerate_backwards

class TestEnumerateBackwards(unittest.TestCase):
    '''Tests the enumerate_backwards function.'''
    def test_enumerate_backwards(self):
        '''Tests the enumerate_backwards function.'''
        data = [1, 2, 3]
        self.assertEqual(list(enumerate_backwards(data)), [(0, 3), (1, 2), (2, 1)])
