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
        stepped = cell.step_forward(0, 0, 0)
        self.assertEqual(len(stepped.layers), 2)

    def test_step_forward_old_layer_top_sinks_after_decomposition(self):
        '''
        When labile sediment decomposes the layer loses mass and its top should sink deeper
        (depths[0] increases) while the bottom stays fixed.
        '''
        c = import_file()[0]
        sc = factory(c)
        initial_top = sc.layers[0].top  # = 0 at start
        stepped = sc.step_forward(dep=1.0, top=c.ro, yrs=1.0, sub_steps=1)
        old_layer = stepped.layers[0]   # layers[0] = original (deepest) layer
        self.assertGreater(old_layer.top, initial_top,
                           'Old layer top must sink (increase) when material is lost to decomposition.')

    def test_step_forward_new_layer_bottom_equals_old_layer_top(self):
        '''
        The new top layer bottom must equal the old layer top — the sediment column has no gaps.
        '''
        c = import_file()[0]
        dep = 1.0
        stepped = factory(c).step_forward(dep=dep, top=c.ro, yrs=1.0, sub_steps=1)
        new_top_layer = stepped.layers[-1]  # layers[-1] = newest (shallowest) layer
        old_layer = stepped.layers[0]       # layers[0] = original (deepest) layer
        self.assertAlmostEqual(new_top_layer.bottom, old_layer.top, places=10,
                               msg='New top layer bottom must equal old layer top: no gap in column.')

    def test_step_forward_new_layer_thickness_equals_deposition_plus_litter(self):
        '''
        The new top layer thickness = dep + litter_length.
        Litter from below-ground biomass (biomass * wa_to_rl * b * yrs) adds organic
        material that occupies physical space on top of the deposited sediment.
        '''
        c = import_file()[0]
        dep = 1.0
        cell = factory(c)
        total_biomass = sum(layer.stocks[0].weight for layer in cell.layers)
        litter_weight = total_biomass * c.wa_to_rl * c.b * 1.0
        litter_length = c.organic_converter_g_to_cm(litter_weight)
        stepped = cell.step_forward(dep=dep, top=c.ro, yrs=1.0, sub_steps=1)
        new_top_layer = stepped.layers[-1]
        self.assertAlmostEqual(new_top_layer.depth, dep + litter_length, places=5,
                               msg='New top layer thickness = dep + litter physical depth.')

    def test_step_forward_new_top_layer_top_is_zero(self):
        '''
        Depths are relative to the current surface.  The newest (shallowest) layer must
        always start at depth 0 so that all depths read as distance below the current ground.
        '''
        c = import_file()[0]
        stepped = factory(c).step_forward(dep=1.0, top=c.ro, yrs=1.0, sub_steps=1)
        self.assertEqual(stepped.layers[-1].top, 0.0,
                         'New top layer top must always be 0 (current surface).')

    def test_step_forward_elevation_changes_after_step(self):
        '''
        Cell elevation must update each step to reflect net gain/loss of surface height.
        With high decomposition (k=0.7142) the surface drops significantly so elevation
        should decrease from the initial value.
        '''
        c = import_file()[0]
        sc = factory(c)
        stepped = sc.step_forward(dep=1.0, top=c.ro, yrs=1.0, sub_steps=1)
        self.assertNotEqual(stepped.elevation, sc.elevation,
                            'Elevation must update after each step.')

    def test_step_forward_new_top_layer_stocks_sum_to_depth(self):
        '''
        In the new top layer, roots occupy space within the deposited sediment
        (documented choice: dep = sediment only; layer thickness = dep + bio.length).
        Equivalently: sediment = dep - bio.length, so stocks sum to layer depth.
        '''
        c = import_file()[0]
        stepped = factory(c).step_forward(dep=1.0, top=c.ro, yrs=1.0, sub_steps=1)
        new_top = stepped.layers[-1]
        stock_sum = (new_top.stocks[0].length + new_top.stocks[1].labile.length
                     + new_top.stocks[1].refractory.length + new_top.stocks[1].inorganic.length)
        self.assertAlmostEqual(stock_sum, new_top.depth, places=5,
                               msg='All stock lengths must sum to layer depth in new top layer.')

class TestCellLayerElevations(unittest.TestCase):
    '''Tests the Cell.layer_elevations property.'''

    def test_initial_cell_layer_elevations_length(self):
        '''Initial cell has 1 layer, so layer_elevations has 2 elements: surface + 1 bottom.'''
        c = import_file()[0]
        sc = factory(c)
        self.assertEqual(len(sc.layer_elevations), 2)

    def test_initial_cell_surface_elevation_is_zero(self):
        '''Initial cell elevation = 0, so layer_elevations[0] == 0.'''
        c = import_file()[0]
        sc = factory(c)
        self.assertEqual(sc.layer_elevations[0], 0.0)

    def test_initial_cell_bottom_elevation(self):
        '''Initial 30 cm layer bottom is 30 cm below surface, so elevation = 0 - 30 = -30.'''
        c = import_file()[0]
        sc = factory(c)
        self.assertAlmostEqual(sc.layer_elevations[1], -30.0, places=10)

    def test_stepped_cell_layer_elevations_length(self):
        '''After one step there are 2 layers, so layer_elevations has 3 elements.'''
        c = import_file()[0]
        stepped = factory(c).step_forward(dep=1.0, top=c.ro, yrs=1.0, sub_steps=1)
        self.assertEqual(len(stepped.layer_elevations), 3)

    def test_stepped_cell_surface_elevation_changed(self):
        '''After one step, surface elevation must differ from 0 (net loss > net gain).'''
        c = import_file()[0]
        stepped = factory(c).step_forward(dep=1.0, top=c.ro, yrs=1.0, sub_steps=1)
        self.assertNotEqual(stepped.layer_elevations[0], 0.0)

    def test_stepped_cell_bottom_elevation_is_minus_30(self):
        '''Original bottom is fixed; deepest layer_elevations value must be -30 cm.'''
        c = import_file()[0]
        stepped = factory(c).step_forward(dep=1.0, top=c.ro, yrs=1.0, sub_steps=1)
        self.assertAlmostEqual(stepped.layer_elevations[-1], -30.0, places=5)

    def test_layer_elevations_are_monotonically_decreasing(self):
        '''Elevations must decrease from surface to bottom (each layer is deeper).'''
        c = import_file()[0]
        stepped = factory(c).step_forward(dep=1.0, top=c.ro, yrs=1.0, sub_steps=1)
        elevs = stepped.layer_elevations
        for i in range(len(elevs) - 1):
            self.assertGreater(elevs[i], elevs[i + 1],
                               f'elevation[{i}]={elevs[i]} should be > elevation[{i+1}]={elevs[i+1]}')


class TestLitterInTopLayer(unittest.TestCase):
    '''Tests that litter from below-ground biomass is added to the top layer each timestep.'''

    def test_top_layer_labile_includes_litter(self):
        '''
        Top layer labile must include litter from below-ground biomass turnover
        (biomass_weight * wa_to_rl * b * fl * yrs) in addition to deposited sediment.
        '''
        c = import_file()[0]  # b=1.0, wa_to_rl=0.1 in morris constants
        cell = factory(c)
        total_biomass = sum(layer.stocks[0].weight for layer in cell.layers)
        dep = 1.0
        yrs = 1.0

        stepped = cell.step_forward(dep=dep, top=c.ro, yrs=yrs)
        new_top = stepped.layers[-1]

        # litter contribution (labile fraction)
        expected_litter_labile = total_biomass * c.wa_to_rl * c.b * c.fl * yrs

        # base sediment labile in the new top layer (deposited sediment minus biomass, labile fraction)
        base_sed_length = max(0.0, dep - new_top.stocks[0].length)
        base_sed_labile_weight = c.organic_converter_cm_to_g(base_sed_length * c.fo * c.fl)

        self.assertAlmostEqual(
            new_top.stocks[1].labile.weight,
            base_sed_labile_weight + expected_litter_labile,
            places=5,
            msg='Top layer labile must include both deposited sediment and litter from biomass turnover.')

