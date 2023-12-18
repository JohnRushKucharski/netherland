'''
Tests that unit test can be found and run in workflow.
'''
import unittest

class TestWorkflow(unittest.TestCase):
    '''
    Tests that unit test discovery and execution.
    '''
    def tests_workflow(self):
        '''
        Tests unit test discovery and execution.
        '''
        val: bool = True
        self.assertTrue(val)
