import unittest

import time

from stats import Stats

class StatsTests(unittest.TestCase):
    '''
    This is the unittest for the stats module
    '''
    def setUp(self):
        self.stats = Stats()

    def test_init(self):
        ''' Test creating stats instance and its defaults '''
        stats = self.stats.get()
        tm = time.time()
        self.assertTrue(isinstance(stats, dict))
        self.assertEqual(len(stats), 1)
        self.assertTrue('created' in stats)
        self.assertAlmostEqual(stats['created'], tm, delta=1)

    def test_set(self):
        ''' Test stats set() method '''
        self.stats.set('name', 123)
        stats = self.stats.get()
        self.assertTrue('name' in stats)
        self.assertEqual(stats['name'], 123)

    def test_add(self):
        ''' Test stats add() method '''
        self.stats.add('name', 123)
        stats = self.stats.get()
        self.assertTrue('name' in stats)
        self.assertEqual(stats['name'], 123)
        self.stats.add('name', 123)
        stats = self.stats.get()
        self.assertEqual(stats['name'], 246)

    def test_set_timestamp(self):
        ''' Test stats set_timestamp() method '''
        tm = time.time()
        self.stats.set_timestamp('name')
        stats = self.stats.get()
        self.assertAlmostEqual(stats['name'], tm, delta=1)

    def test_set_subnames(self):
        ''' Test name1/name2/../nameN type names '''
        self.stats.set('name1/name2', 12)
        self.stats.set('name1/name3', 23)
        stats = self.stats.get()
        self.assertTrue('name1' in stats)
        self.assertTrue('name2' in stats['name1'])
        self.assertEqual(stats['name1']['name2'], 12)
        self.assertTrue('name3' in stats['name1'])
        self.assertEqual(stats['name1']['name3'], 23)
        self.assertRaises(Exception, self.stats.set, 'name1', 123)
        self.assertRaises(Exception, self.stats.set, 'name1/name2/name3', 123)
