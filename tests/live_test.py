'''
Tests the live.py module.
'''
import unittest

from src.constants import import_file
from src.live import (distribution_builder, integration_builder,
                      turnover_builder, erosion_builder, burial_builder)

test_constants = import_file()[0]

class TestDistributionBuilder(unittest.TestCase):
    '''
    Tests the distribution_builder function.
    '''
    def test_distribution_builder_returns_callable(self):
        '''
        Tests the distribution_builder function returns a callable.
        '''
        self.assertTrue(callable(distribution_builder(test_constants)))

class TestPartialDistribution(unittest.TestCase):
    '''
    Tests the partial distribution function.
    
    A closure that is returned by the distribution_builder function.
    '''
    def test_partial_distribution_returns_callable(self):
        '''
        Tests the distribution_builder function returns a function.
        '''
        self.assertTrue(callable(distribution_builder(test_constants)(1.0)))
    def test_partial_distribution_top_less_than_0_raises_value_error(self):
        '''
        Depth less than 0 raises ValueError.
        '''
        f = distribution_builder(test_constants)
        with self.assertRaises(ValueError):
            f(-1.0)

class TestDistribution(unittest.TestCase):
    '''
    Tests the distribution function.
    
    A closure that is returned by the distribution_builder->partial_distribution function.
    '''
    def test_distribution_returns_float(self):
        '''
        Tests the distribution function returns a float.
        '''
        dist = distribution_builder(test_constants)(1.0)
        self.assertTrue(isinstance(dist(1.0), float))
    def test_distribution_depth_less_than_0_raises_value_error(self):
        '''
        Depth less than 0 raises ValueError.
        '''
        f = distribution_builder(test_constants)(1.0)
        with self.assertRaises(ValueError):
            f(-1.0)
    def test_distribution_depth_equal_to_0_returns_top(self):
        '''
        Depth equal to 0 returns top.
        '''
        f = distribution_builder(test_constants)(1.0)
        self.assertEqual(f(depth=0.0), 1.0)
    def test_distribution_depth_equal_to_rd_returns_0(self):
        '''
        Depth equal to root depth returns near 0.
        '''
        f = distribution_builder(test_constants)(1.0)
        self.assertAlmostEqual(f(depth=test_constants.rd), 0.04978706836786395)
    def test_distribution_depth_gt_rd_returns_0(self):
        '''
        Depth greater than root depth returns 0.
        '''
        f = distribution_builder(test_constants)(1.0)
        self.assertAlmostEqual(f(test_constants.rd + 1), 0)
    def test_distribution_no_biomass_at_top_returns_0_at_0_depth(self):
        '''
        No biomass at surface returns 0 at surface.
        '''
        f = distribution_builder(test_constants)(0.0)
        self.assertAlmostEqual(f(depth=0.0), 0.0)
    def test_distribution_no_biomass_at_top_returns_0_at_1_depth(self):
        '''
        No biomass at surface returns 0 at surface.
        '''
        f = distribution_builder(test_constants)(0.0)
        self.assertAlmostEqual(f(depth=1.0), 0.0)
    def test_biomass_at_depth_1_biomass_returns_approx_0_9_at_1_depth(self):
        '''
        1 biomass at surface returns 0.9 at 1 depth, with k1=0.1.
        
        Note: This is less than the biomass at the surface, because calculus :).
        '''
        f = distribution_builder(test_constants)(1.0)
        self.assertAlmostEqual(f(depth=1.0), 0.9, places=2)

class TestIntegrationBuilder(unittest.TestCase):
    '''
    Tests the integration_builder function.
    '''
    def test_integration_builder_returns_callable(self):
        '''
        Tests the integration_builder function returns a callable.
        '''
        self.assertTrue(callable(integration_builder(test_constants)))

class TestPartialIntegration(unittest.TestCase):
    '''
    Tests the partial integration function.
    
    A closure that is returned by the integration_builder function.
    '''
    def test_partial_integration_returns_callable(self):
        '''
        Tests the integration_builder function returns a function.
        '''
        self.assertTrue(callable(integration_builder(test_constants)(1.0)))

class TestIntegration(unittest.TestCase):
    '''
    Tests the integration function.
    
    A closure that is returned by the integration_builder->partial_integration function.
    '''
    def test_integration_returns_float(self):
        '''
        Tests the integration function returns a float.
        '''
        dist = distribution_builder(test_constants)(1.0)
        f = integration_builder(test_constants)(dist)
        self.assertTrue(isinstance(f((0,1)), float))
    def test_integration_depths_less_than_0_raises_value_error(self):
        '''
        Depth less than 0 raises ValueError.
        '''
        dist = distribution_builder(test_constants)(1.0)
        f = integration_builder(test_constants)(dist)
        with self.assertRaises(ValueError):
            f((0, -1.0))
    def test_integration_ascending_depths_raises_value_error(self):
        '''
        Ascending depths raises ValueError.
        '''
        dist = distribution_builder(test_constants)(1.0)
        f = integration_builder(test_constants)(dist)
        with self.assertRaises(ValueError):
            f((1.0, 0))
    def test_integration_depths_equal_to_0_returns_0(self):
        '''
        Depths equal to 0 returns 0.
        '''
        dist = distribution_builder(test_constants)(1.0)
        f = integration_builder(test_constants)(dist)
        self.assertAlmostEqual(f((0, 0)), 0.0)

    def test_integration_first_increment_between_0_and_top(self):
        '''
        First increment of integration is between 0 and top.
        '''
        top = 1.0
        dist = distribution_builder(test_constants)(top)
        val = integration_builder(test_constants)(dist)((0.0, 1.0))
        self.assertLess(val, 1.0)
        self.assertGreater(val, 0.0)

    def test_expose_default_biomass_over_rd_per_unit_at_top(self):
        '''
        Exposes default biomass over rd per unit at top.
        
        Each unit of biomass as surface given Morris default
        parameters for k, and rd produces ~9.5 g of biomass per cm2 cell.
        '''
        top = 1.0
        dist = distribution_builder(test_constants)(top)
        val = integration_builder(test_constants)(dist)((0.0, test_constants.rd))
        self.assertAlmostEqual(val, 9.50, 2)

class TestTurnoverBuilder(unittest.TestCase):
    '''
    Tests the turnover_builder function.
    '''
    def test_turnover_builder_returns_callable(self):
        '''
        Tests the turnover_builder function returns a callable.
        '''
        self.assertTrue(callable(turnover_builder(test_constants)))

class TestTurnover(unittest.TestCase):
    '''
    Tests the turnover function.
    '''
    def test_turnover_returns_tuple(self):
        '''
        Tests the turnover function returns a tuple.
        '''
        turnover = turnover_builder(test_constants)
        self.assertTrue(isinstance(turnover(weight=1.0, years=1.0), tuple))
    def test_turnover_negative_weight_raises_value_error(self):
        '''
        Negative weight raises ValueError.
        '''
        turnover = turnover_builder(test_constants)
        with self.assertRaises(ValueError):
            turnover(weight=-1.0, years=1.0)
    def test_turnover_negative_years_raises_value_error(self):
        '''
        Negative years raises ValueError.
        '''
        turnover = turnover_builder(test_constants)
        with self.assertRaises(ValueError):
            turnover(weight=1.0, years=-1.0)
    def test_turnover_zero_weight_returns_zeros(self):
        '''
        Zero weight returns zeros.
        '''
        turnover = turnover_builder(test_constants)
        self.assertEqual(turnover(weight=0.0, years=1.0), (0.0, 0.0, 0.0))
    def test_turnover_zero_years_returns_zeros(self):
        '''
        Zero years returns zeros.
        '''
        turnover = turnover_builder(test_constants)
        self.assertEqual(turnover(weight=1.0, years=0.0), (0.0, 0.0, 0.0))
    def test_turnover_sum_is_k2_weight(self):
        '''
        Sum of turnover is k2 * weight.
        '''
        weight = 1.0
        turnover = turnover_builder(test_constants)
        self.assertEqual(sum(turnover(weight=weight, years=1.0)), test_constants.k2 * weight)
    def test_turnover_expose_default_rate_of_turnover(self):
        '''
        Exposes default rate of turnover.
        
        With default parameters, half of biomass is turned over each year.
        '''
        weight = 1.0
        turnover = turnover_builder(test_constants)
        self.assertEqual(sum(turnover(weight=weight, years=1.0)), weight/2)

class TestErosionBuilder(unittest.TestCase):
    '''
    Tests the erosion_builder function.
    '''
    def test_erosion_builder_returns_callable(self):
        '''
        Tests the erosion_builder function returns a callable.
        '''
        self.assertTrue(callable(erosion_builder(test_constants)))

class TestPartialErosion(unittest.TestCase):
    '''Tests the partial erosion function.'''
    def test_partial_erosion_returns_callable(self):
        '''Tests the erosion_builder function returns a function.'''
        self.assertTrue(callable(erosion_builder(test_constants)(lambda x: x)))
    def test_partial_erosion_returns_callable_w_integration_fx(self):
        '''Tests the erosion_builder function returns a function.'''
        self.assertTrue(callable(erosion_builder(test_constants)(integration_builder(test_constants)(distribution_builder(test_constants)(1.0))))) # pylint: disable=line-too-long

class TestErosion(unittest.TestCase):
    '''Tests the erosion function.'''
    # pylint: disable=line-too-long
    def test_erosion_returns_tuple(self):
        '''Tests the erosion function returns a tuple.'''
        integration = integration_builder(test_constants)(distribution_builder(test_constants)(1.0))
        erosion = erosion_builder(test_constants)(integration)
        self.assertTrue(isinstance(erosion((0, 1), 1), tuple))
    def test_erosion_negative_depth_raises_value_error(self):
        '''Tests the erosion function raises ValueError with negative depth.'''
        erosion = erosion_builder(test_constants)(integration_builder(test_constants)(distribution_builder(test_constants)(1.0)))
        with self.assertRaises(ValueError):
            erosion((-1.0, 1), 1.0)
    def test_erosion_negative_weight_raises_value_error(self):
        '''Tests the erosion function raises ValueError with negative weight.'''
        erosion = erosion_builder(test_constants)(integration_builder(test_constants)(distribution_builder(test_constants)(1.0)))
        with self.assertRaises(ValueError):
            erosion((0, 1), -1.0)
    def test_erosion_output_sums_to_biomass_increment_of_depth(self):
        '''Tests the erosion function output sums to biomass weight in eroded depth.'''
        integration = integration_builder(test_constants)(distribution_builder(test_constants)(1.0))
        erosion = erosion_builder(test_constants)(integration)
        self.assertAlmostEqual(sum(erosion((0, 1), erosion=1.0)), integration((0, 1)), 4)
    def test_erosion_output_sums_to_biomass_in_depth(self):
        '''Tests the erosion function output sums to biomass weight in eroded depth.'''
        integration = integration_builder(test_constants)(distribution_builder(test_constants)(1.0))
        erosion = erosion_builder(test_constants)(integration)
        self.assertAlmostEqual(sum(erosion((0, 1), erosion=10)), integration((0, 10)), 4)

class TestBurialBuilder(unittest.TestCase):
    '''
    Tests the burial_builder function.
    '''
    def test_burial_builder_returns_callable(self):
        '''
        Tests the burial_builder function returns a callable.
        '''
        self.assertTrue(callable(burial_builder(test_constants)))

class TestPartialBurial(unittest.TestCase):
    '''Tests the partial burial function.'''
    def test_partial_burial_returns_callable(self):
        '''Tests the burial_builder function returns a function.'''
        self.assertTrue(callable(burial_builder(test_constants)(lambda x: x)))
    def test_partial_burial_returns_callable_w_integration_fx(self):
        '''Tests the burial_builder function returns a function.'''
        self.assertTrue(callable(burial_builder(test_constants)(integration_builder(test_constants)(distribution_builder(test_constants)(1.0))))) # pylint: disable=line-too-long

class TestBurial(unittest.TestCase):
    '''Tests the burial function.'''
    def test_burial_returns_tuple(self):
        '''Tests the burial function returns a tuple.'''
        integration = integration_builder(test_constants)(distribution_builder(test_constants)(1.0))
        burial = burial_builder(test_constants)(integration)
        self.assertTrue(isinstance(burial((0, 1), 1), tuple))
    def test_burial_negative_depth_raises_value_error(self):
        '''Tests the burial function raises ValueError with negative depth.'''
        integration = integration_builder(test_constants)(distribution_builder(test_constants)(1.0))
        burial = burial_builder(test_constants)(integration)
        with self.assertRaises(ValueError):
            burial((-1.0, 1), 1.0)
    def test_burial_descending_depth_raises_value_error(self):
        '''Tests the burial function raises ValueError with descending depth.'''
        integration = integration_builder(test_constants)(distribution_builder(test_constants)(1.0))
        burial = burial_builder(test_constants)(integration)
        with self.assertRaises(ValueError):
            burial((1, 0), 1.0)
    def test_burial_negative_deposition_raises_value_error(self):
        '''Tests the burial function raises ValueError with negative deposition.'''
        integration = integration_builder(test_constants)(distribution_builder(test_constants)(1.0))
        burial = burial_builder(test_constants)(integration)
        with self.assertRaises(ValueError):
            burial((0, 1), -1.0)
    def test_burial_output_sums_to_biomass_increment_of_depth(self):
        '''Tests the burial function output sums to biomass weight in deposited depth.'''
        integration = integration_builder(test_constants)(distribution_builder(test_constants)(1.0))
        expected = integration((test_constants.rd - 1, test_constants.rd))
        burial = burial_builder(test_constants)(integration)
        actual = burial((test_constants.rd - 1, test_constants.rd), deposition=2.0)
        self.assertAlmostEqual(sum(actual), expected, 4)
