import unittest

from globallist import GlobalList

class MemberClass(object):
    def __init__(self, id, listinstance):
        self.id = id
        self.listinstance = listinstance

class DerivedGlobalList(GlobalList):
    def getMemberClass(self):
        return MemberClass

class GlobalListTests(unittest.TestCase):
    '''
    This is the unittest for the uniscada.globallist module
    '''
    def setUp(self):
        self.globallist = DerivedGlobalList()

    def test_class_name(self):
        ''' Test member class '''
        self.assertEqual(self.globallist.getMemberClass(), MemberClass)

    def test_member_id(self):
        ''' Test member instance setup '''
        id1 = self.globallist.find_by_id('A')
        self.assertEqual(id1.id, 'A')
        self.assertEqual(id1.listinstance, self.globallist)

    def test_add_member(self):
        ''' Test member add and lookup '''
        id1 = self.globallist.find_by_id('A')
        id2 = self.globallist.find_by_id('B')
        id3 = self.globallist.find_by_id('A')
        self.assertTrue(isinstance(id1, MemberClass))
        self.assertNotEqual(id1, id2)
        self.assertEqual(id1, id3)
        self.assertTrue(isinstance(id3, MemberClass))

    def test_remove_member(self):
        ''' Test member remove '''
        id1 = self.globallist.find_by_id('A')
        self.globallist.remove_by_id('A')
        id2 = self.globallist.find_by_id('B')
        id3 = self.globallist.find_by_id('A')
        self.assertTrue(isinstance(id1, MemberClass))
        self.assertNotEqual(id1, id2)
        self.assertNotEqual(id1, id3)
        self.assertTrue(isinstance(id3, MemberClass))

    def test_member_list(self):
        ''' Test member list generator '''
        id1 = self.globallist.find_by_id('A')
        id2 = self.globallist.find_by_id('B')
        id3 = self.globallist.find_by_id('A')
        self.assertItemsEqual(['A', 'B'], list(self.globallist.get_id_list()))
