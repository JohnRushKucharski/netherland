'''
Tests for the constants module.
'''
import unittest
from pathlib import Path

from src.constants import MORRIS_CONSTANTS, import_file, parse_ids, parse_var, Constants

class TestMorrisConstants(unittest.TestCase):
    '''Tests the path of the default constants file.'''
    def test_path_exists(self):
        '''Tests the path of the default constants file exists.'''
        path = Path(MORRIS_CONSTANTS)
        self.assertTrue(Path.exists(path))

class TestParseIds(unittest.TestCase):
    '''Tests the parse_ids function.'''
    def test_elipse(self):
        '''Tests the parse_ids function with an elipse.'''
        ids = [1, '...', 10]
        self.assertEqual(parse_ids(ids), tuple(range(1, 11)))
    def test_list(self):
        '''Tests the parse_ids function with a list.'''
        ids = [1, 2, 3]
        self.assertEqual(parse_ids(ids), tuple(ids))
    def test_non_integer_with_elipse(self):
        '''Tests the parse_ids function with a non-integer.'''
        ids = [1, '...', 'a']
        with self.assertRaises(TypeError):
            parse_ids(ids)
    def test_too_many_values_after_elipse(self):
        '''Tests the parse_ids function with too many values after an elipse.'''
        ids = [1, '...', 2, 3]
        with self.assertRaises(ValueError):
            parse_ids(ids)
    def test_non_integer_without_elipse(self):
        '''Tests the parse_ids function with a non-integer.'''
        ids = [1, 'a', 3]
        with self.assertRaises(ValueError):
            parse_ids(ids)
    def test_duplicate_ids_raise_value_error(self):
        '''Tests the parse_ids function with duplicate ids.'''
        ids = [1, 1, 3]
        with self.assertRaises(ValueError):
            parse_ids(ids)

class TestParseSurfaceAreas(unittest.TestCase):
    '''Tests the parse_surface_areas function.'''
    def test_elipse(self):
        '''Tests the parse_surface_areas function with an elipse.'''
        surface_areas = [1, '...']
        self.assertEqual(parse_var(surface_areas, 10), tuple([1] * 10))
    def test_list(self):
        '''Tests the parse_surface_areas function with a list.'''
        surface_areas = [1, 2, 3]
        self.assertEqual(parse_var(surface_areas, 3), tuple(surface_areas))
    def test_too_many_values_after_elipse(self):
        '''Tests the parse_surface_areas function with too many values after an elipse.'''
        surface_areas = [1, '...', 2, 3]
        with self.assertRaises(ValueError):
            parse_var(surface_areas, 10)
    def test_invalid_number_of_surface_areas(self):
        '''Tests the parse_surface_areas function with an invalid number of surface areas.'''
        surface_areas = [1, 2, 3]
        with self.assertRaises(ValueError):
            parse_var(surface_areas, 10)

class TestImportFile(unittest.TestCase):
    '''Tests the import file function.'''
    def test_import_file(self):
        '''Tests the import file returns constants.'''
        data = import_file(MORRIS_CONSTANTS)
        self.assertIsInstance(data[0], Constants)

class TestConstants(unittest.TestCase):
    '''Tests the Constants class.'''
    def test_default_attributes_initialized(self):
        '''Tests that the default objects attributes are initialized with appropriate types.'''
        is_ok:bool = True
        test_obj = import_file()[0]
        for k, val in test_obj.__dict__.items():
            if k.startswith('__') or str(val).startswith('<function'):
                continue
            else:
                if k == 'id':
                    if not isinstance(val, int):
                        is_ok = False
                else:
                    if not isinstance(val, float):
                        is_ok = False
        self.assertTrue(is_ok)

    def test_organic_converter_g_to_cm(self):
        '''Test g to cm3 converter is callable.'''
        self.assertTrue(callable(import_file()[0].organic_converter_g_to_cm))

    def test_inorganic_converter_g_to_cm_1g_is_10cm(self):
        '''
        Exposes Morris constant g to cm conversion:
        
        A 1 cm3 volume weights 0.1 g (per the Morris & Bowden constants).
        Equivalently, there are 10 cm3 per 1 g of inorganic material.
        1 cm3 is 1/1,000,000 (less than a teaspoon) of a cubic meter.
        So, 1 g of inorganic material in a 1 cm2 surface would be 10 cm deep.
        '''
        self.assertEqual(import_file()[0].inorganic_converter_g_to_cm(1), 10)

    def test_organic_converter_g_to_cm_0d1g_is_1d392cm(self):
        '''
        Exposes Morris constant g to cm conversion:
        
        A 1 cm3 volume weights 0.07182 g (per the Morris & Bowden constants).
        Equivalently there are 13.92 cm3 per 1 g of organic material.
        So, 0.1 g of inorganic material in a 1 cm2 grid would be 1.392 cm deep.
        '''
        self.assertAlmostEqual(import_file()[0].organic_converter_g_to_cm(0.1), 1.392, 3)

    def test_describe_cm3_to_g_conversion(self):
        '''
        1 kg of organic material takes up approximatly 13.923 liters (>3.5 gallons) of space.
        '''
        self.assertAlmostEqual(import_file()[0].organic_g_to_cm3 * 1000, 13923, -1)
