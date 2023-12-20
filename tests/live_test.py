'''
Tests the live.py module.
'''
import unittest

from src.constants import import_file
from src.live import distribution_builder

test_constants = import_file()[0]

class TestDistributionBuilder(unittest.TestCase):
    '''
    Tests the distribution_builder function.
    '''
    def tests_distribution_builder_returns_callable(self):
        '''
        Tests the distribution_builder function returns a callable.
        '''
        self.assertTrue(callable(distribution_builder(test_constants)))
    def tests_distribution_builder_partial_returns_callable(self):
        '''
        Tests the distribution_builder function returns a function.
        '''
        self.assertTrue(callable(distribution_builder(test_constants)(1.0)))

class TestDistribution(unittest.TestCase):
    '''
    Tests the distribution function.
    '''
    def tests_distribution_returns_tuple(self):
        '''
        Tests the distribution function returns a tuple.
        '''
        dist = distribution_builder(test_constants)(1.0)
        self.assertTrue(isinstance(dist(1.0), float))
