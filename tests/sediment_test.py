'''
Unit tests for sediment.py module.
'''
import unittest

from src.constants import import_file
from src import sediment as sed
from src.stock import Measurement


def _make_sediments(depth_cm: float = 10.0) -> sed.Sediments:
    '''Helper: create a Sediments object from a length (cm) using morris constants.'''
    tools = sed.Tools(import_file()[0])
    return sed.factory(depth_cm, tools, Measurement.LENGTH)


class TestSedimentsTransfers(unittest.TestCase):
    '''Tests that transfers() correctly removes material from the layer.'''

    def test_labile_decreases_after_decomposition(self):
        '''Labile organic sediment is consumed by decomposition and must decrease after transfers().'''
        sediments = _make_sediments()
        before = sediments.labile.weight
        after = sediments.transfers(biomass_weight=1.0, yrs=1.0).labile.weight
        self.assertLess(after, before,
                        msg='Labile should decrease due to decomposition (bacteria break it down '
                            'and the mass leaves the layer as CO2, CH4, nutrients, etc.).')

    def test_inorganic_decreases_after_ash_uptake(self):
        '''Inorganic ash is taken up by above-ground biomass production and must decrease after transfers().'''
        sediments = _make_sediments()
        before = sediments.inorganic.weight
        after = sediments.transfers(biomass_weight=1.0, yrs=1.0).inorganic.weight
        self.assertLess(after, before,
                        msg='Inorganic should decrease due to ash uptake out of the layer.')

    def test_refractory_unchanged_by_transfers(self):
        '''Refractory sediment is non-reactive and must not change during transfers().'''
        sediments = _make_sediments()
        before = sediments.refractory.weight
        after = sediments.transfers(biomass_weight=1.0, yrs=1.0).refractory.weight
        self.assertAlmostEqual(after, before, places=10,
                               msg='Refractory should be unchanged by transfers().')


class TestSedimentsTransfersBiomassWeight(unittest.TestCase):
    '''Tests that transfers() uses biomass weight (not inorganic weight) for ash uptake.'''

    def test_transfers_accepts_biomass_weight_parameter(self):
        '''transfers() must accept biomass_weight as first argument (new signature).'''
        sediments = _make_sediments()
        # Must not raise TypeError — currently will because signature is transfers(yrs)
        _ = sediments.transfers(biomass_weight=1.0, yrs=1.0)

    def test_ash_removal_proportional_to_biomass_not_inorganic(self):
        '''
        Ash removal = k3 * biomass_weight * wa_to_rl * yrs.
        When biomass_weight differs from inorganic_weight the two approaches
        give different answers; this test pins the correct (biomass) formula.
        '''
        c = import_file()[0]
        sediments = _make_sediments(10.0)
        biomass_weight = sediments.inorganic.weight * 20.0  # deliberately different
        before = sediments.inorganic.weight
        after = sediments.transfers(biomass_weight=biomass_weight, yrs=1.0).inorganic.weight
        expected_removal = c.k3 * biomass_weight * c.wa_to_rl * 1.0
        self.assertAlmostEqual(before - after, expected_removal, places=6,
                               msg='Ash removed must equal k3 * biomass_weight * wa_to_rl * yrs.')

    def test_zero_biomass_removes_no_inorganic_ash(self):
        '''With zero biomass no above-ground production occurs so no ash is taken up.'''
        sediments = _make_sediments(10.0)
        before = sediments.inorganic.weight
        after = sediments.transfers(biomass_weight=0.0, yrs=1.0).inorganic.weight
        self.assertAlmostEqual(before, after, places=10,
                               msg='No biomass → no ash uptake → inorganic must be unchanged.')


class TestLitter(unittest.TestCase):
    '''Tests the litter function on sed.Tools.'''

    def test_litter_function_exists_on_tools(self):
        '''sed.Tools must expose a litter callable.'''
        tools = sed.Tools(import_file()[0])
        self.assertTrue(callable(tools.litter),
                        msg='sed.Tools must have a litter function.')

    def test_litter_returns_labile_refractory_inorganic_tuple(self):
        '''litter() must return a 3-tuple (labile, refractory, inorganic) in grams.'''
        tools = sed.Tools(import_file()[0])
        result = tools.litter(biomass_weight=1.0, yrs=1.0)
        self.assertEqual(len(result), 3)

    def test_litter_zero_when_biomass_zero(self):
        '''No biomass → no above-ground production → no litter.'''
        tools = sed.Tools(import_file()[0])
        labile, refractory, inorganic = tools.litter(biomass_weight=0.0, yrs=1.0)
        self.assertEqual(labile, 0.0)
        self.assertEqual(refractory, 0.0)
        self.assertEqual(inorganic, 0.0)

    def test_litter_labile_matches_formula(self):
        '''litter labile = biomass_weight * wa_to_rl * b * fl * yrs.'''
        c = import_file()[0]
        tools = sed.Tools(c)
        biomass_weight = 2.0
        yrs = 1.0
        labile, _, _ = tools.litter(biomass_weight=biomass_weight, yrs=yrs)
        expected = biomass_weight * c.wa_to_rl * c.b * c.fl * yrs
        self.assertAlmostEqual(labile, expected, places=10)

    def test_litter_refractory_matches_formula(self):
        '''litter refractory = biomass_weight * wa_to_rl * b * fc * yrs.'''
        c = import_file()[0]
        tools = sed.Tools(c)
        biomass_weight = 2.0
        yrs = 1.0
        _, refractory, _ = tools.litter(biomass_weight=biomass_weight, yrs=yrs)
        expected = biomass_weight * c.wa_to_rl * c.b * c.fc * yrs
        self.assertAlmostEqual(refractory, expected, places=10)

    def test_litter_inorganic_is_zero(self):
        '''Litter is organic plant material — no inorganic component.'''
        tools = sed.Tools(import_file()[0])
        _, _, inorganic = tools.litter(biomass_weight=1.0, yrs=1.0)
        self.assertEqual(inorganic, 0.0)


class TestSedimentsErosion(unittest.TestCase):
    '''Tests that erosion() correctly removes material from the layer.'''

    def test_erosion_removes_labile(self):
        '''Erosion carries sediment away — labile must decrease when erosion > 0.'''
        sediments = _make_sediments(10.0)
        before = sediments.labile.weight
        after = sediments.erosion(5.0).labile.weight   # erode half the layer
        self.assertLess(after, before,
                        msg='Labile should decrease when sediment is eroded away.')

    def test_erosion_removes_refractory(self):
        '''Erosion carries sediment away — refractory must decrease when erosion > 0.'''
        sediments = _make_sediments(10.0)
        before = sediments.refractory.weight
        after = sediments.erosion(5.0).refractory.weight
        self.assertLess(after, before,
                        msg='Refractory should decrease when sediment is eroded away.')

    def test_erosion_removes_inorganic(self):
        '''Erosion carries sediment away — inorganic must decrease when erosion > 0.'''
        sediments = _make_sediments(10.0)
        before = sediments.inorganic.weight
        after = sediments.erosion(5.0).inorganic.weight
        self.assertLess(after, before,
                        msg='Inorganic should decrease when sediment is eroded away.')

    def test_zero_erosion_leaves_sediments_unchanged(self):
        '''Erosion of 0 (or negative, i.e. deposition) must leave sediments unchanged.'''
        sediments = _make_sediments(10.0)
        self.assertEqual(sediments.erosion(0.0), sediments)
        self.assertEqual(sediments.erosion(-1.0), sediments)
