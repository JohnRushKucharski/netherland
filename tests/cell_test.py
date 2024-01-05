'''
Unit tests for cell.py module.
'''
import unittest

import numpy as np

from src.constants import import_file
from src.live import PartialTools
from src.cell import enumerate_backwards, initial_layer, Layer, factory, Cell

class TestEnumerateBackwards(unittest.TestCase):
    '''Tests the enumerate_backwards function.'''
    def test_enumerate_backwards(self):
        '''Tests the enumerate_backwards function.'''
        data = [1, 2, 3]
        self.assertEqual(list(enumerate_backwards(data)), [(0, 3), (1, 2), (2, 1)])

class TestInitialLayer(unittest.TestCase):
    '''Tests the initial_layer function.'''
    # pylint: disable=line-too-long
    def test_initial_layer_depth(self):
        '''Tests the initial_layer with morris constants has depth of 30cm.'''
        self.assertEqual(initial_layer(import_file()[0]).depth, 30)
    def test_initial_layer_has_expected_number_of_stocks(self):
        '''Tests the initial_layer with morris constants has expected number of stocks.'''
        self.assertEqual(len(initial_layer(import_file()[0]).stocks), 2)
    def test_initial_layer_length_of_stocks_is_30_cm(self):
        '''Tests the initial_layer with morris constants has expected length of stocks.'''
        init = initial_layer(import_file()[0])
        lengths = np.sum([stock.length for stock in init.stocks])
        self.assertEqual(lengths, 30)
    def test_initial_layer_morris_constant_biomass_is_approx_0_10_g(self):
        '''Exposes morris constant biomass weight is ~ 0.10 g in 30cm (root zone).'''
        self.assertAlmostEqual(initial_layer(import_file()[0]).stocks[0].weight, 0.10, 2)
    def test_initial_layer_morris_constant_biomass_is_approx_1_39_cm(self):
        '''Exposes morris constant biomass length is ~ 1.39 cm in 30cm (root zone).'''
        exp = import_file()[0].organic_converter_g_to_cm(0.10)
        self.assertAlmostEqual(initial_layer(import_file()[0]).stocks[0].length, exp, 2)
    def test_initial_layer_morris_constant_sediments_is_approx_28_61_cm(self):
        '''Exposes morris constant sediments length, 28.61 cm, in 30cm (root zone - biomass length).'''
        self.assertAlmostEqual(initial_layer(import_file()[0]).stocks[1].length, 28.61, 2)
    def test_initial_layer_morris_constant_sediments_is_approx_2_19_g(self):
        '''Exposes morris constant sediments weight, is approx 2.19 g in 30cm ().'''
        self.assertAlmostEqual(initial_layer(import_file()[0]).stocks[1].weight, 2.19, 2)
    def test_initial_layer_biomass_stock_has_expected_weight(self):
        '''Tests the initial_layer with morris constants has expected biomass weight.'''
        c = import_file()[0]
        exp = PartialTools(c).make_tools(c.ro).integration((0, c.depth)) # ~ 0.10
        self.assertAlmostEqual(initial_layer(c).stocks[0].weight, exp, 2)

class TestLayer(unittest.TestCase):
    '''Tests the Layer class.'''
    def test_layer_depth(self):
        '''Tests the layer depth.'''
        self.assertEqual(Layer((0, 10), (0, 0)).depth, 10)
    def test_step_forward_raises_value_error_if_yrs_is_negative(self):
        '''Tests the step_forward function raises error if yrs is negative.'''
        layer = Layer((0, 1), (0, 0))
        with self.assertRaises(ValueError):
            layer.step_forward(0, 0, -1)
    def test_step_forward_raises_value_error_if_biomass_is_negative(self):
        '''Tests the step_forward function raises error if deposition is negative.'''
        layer = Layer((0, 1), (0, 0))
        with self.assertRaises(ValueError):
            layer.step_forward(0, -1, 0)
    def test_step_forward_raises_value_error_if_erosion_gt_depth(self):
        '''Tests the step_forward function raises error if deposition is negative.'''
        layer = Layer((0, 1), (0, 0))
        with self.assertRaises(ValueError):
            layer.step_forward(-1.1, 0, 0)
    def test_step_forward_yrs_0_returns_layer_with_no_change(self):
        '''
        Tests the step_forward function returns a layer with no change 
        if yrs is 0, dep is 0 and biomass is no change.
        '''
        cons = import_file()[0]
        init_layer = initial_layer(cons)
        self.assertEqual(init_layer.step_forward(0, cons.ro, 0), init_layer)
    def test_step_forward_erosion_eq_depth_returns_empty_layer(self):
        '''Tests the step_forward function returns an empty layer if erosion equals depth.'''
        init_layer = initial_layer(import_file()[0])
        self.assertEqual(init_layer.step_forward(-init_layer.depth, 0, 0).depth, 0)

class TestFactory(unittest.TestCase):
    '''Tests the factory function.'''
    def test_factory(self):
        '''Tests the factory function returns a Cell.'''
        self.assertIsInstance(factory(import_file()[0]), Cell)
    def test_factory_creates_cell_w_single_bottom_layer(self):
        '''Tests the factory function returns a Cell with expected number of layers.'''
        self.assertEqual(len(factory(import_file()[0]).layers), 1)
    def test_factory_creates_cell_with_elevation_defined_in_import_file(self):
        '''Tests the factory function returns a Cell with expected elevation.'''
        self.assertEqual(factory(import_file()[0]).elevation, import_file()[0].du)

class TestCell(unittest.TestCase):
    '''Tests the Cell class.'''
    def test_step_forward_raises_value_error_if_yrs_is_negative(self):
        '''Tests the step_forward function raises error if yrs is negative.'''
        with self.assertRaises(ValueError):
            factory(import_file()[0]).step_forward(0, 0, -1)
    def test_step_forward_raises_value_error_if_top_is_negative(self):
        '''Tests the step_forward function raises error if biomass at top is negative.'''
        with self.assertRaises(ValueError):
            factory(import_file()[0]).step_forward(0, -1, 1)
    def test_step_forward_0_deposition_adds_new_empty_layer(self):
        '''Tests the step_forward function adds a new empty layer if deposition is 0.'''
        cell = factory(import_file()[0])
        cell.step_forward(0, 0, 0)
        self.assertEqual(len(cell.layers), 2)
