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
