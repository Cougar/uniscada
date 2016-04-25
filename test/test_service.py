import unittest
import time

from service import Service

class ServiceTests(unittest.TestCase):
    '''
    This is the unittest for the uniscada.service module
    '''
    def setUp(self):
        self.service = Service('SWS')
        self.setup = {
            "conv_coef": "",
            "desc0": "Test 3 var control (do, ext1, ext2, ext3):",
            "desc1": "Test 3 var control (do, ext1, ext2, ext3):",
            "desc2": "Test 3 var control (do, ext1, ext2, ext3):",
            "freshness": "yes",
            "grp_value": "1",
            "in_unit": "",
            "min_len": "",
            "minstep": "",
            "multicfg": "2 3 4",
            "multiperf": "Sout Sext1 Sext2 Sext3",
            "multivalue": "1 2 3 4",
            "notify": "none",
            "out_unit": "",
            "sta_reg": "SWS",
            "step": "5",
            "svc_name": "TestJuhtW",
            "toggle": "",
            "val_reg": "SWW",
        }

        self.service_data_v1 = {
            "description": [
                {
                    "desc": "Test 3 var control (do, ext1, ext2, ext3): {{ Sout.val }} {{ Sext1.val }} {{ Sext2.val }} {{ Sext3.val }}",
                    "status": 0
                },
                {
                    "desc": "Test 3 var control (do, ext1, ext2, ext3): {{ Sout.val }} {{ Sext1.val }} {{ Sext2.val }} {{ Sext3.val }}",
                    "status": 1
                },
                {
                    "desc": "Test 3 var control (do, ext1, ext2, ext3): {{ Sout.val }} {{ Sext1.val }} {{ Sext2.val }} {{ Sext3.val }}",
                    "status": 2
                }
            ],
            "key": "SWW",
            "multiperf": [
                {
                    "cfg": False,
                    "name": "Sout"
                },
                {
                    "cfg": True,
                    "name": "Sext1"
                },
                {
                    "cfg": True,
                    "name": "Sext2"
                },
                {
                    "cfg": True,
                    "name": "Sext3"
                }
            ],
            "show": True,
            "svc_name": "TestJuhtW"
        }
        self.service.set_setup(self.setup)

    def test_id(self):
        ''' Test service id '''
        self.assertEqual(self.service.get_id(), 'SWS')

    def test_setup(self):
        ''' Test controller setup '''
        self.assertDictEqual(self.setup, self.service.get_setup())

    def test_get_service_data_v1(self):
        ''' Test API v1 service data output '''
        self.assertDictEqual(self.service_data_v1, self.service.get_service_data_v1())

    def test_setupmask(self):
        ''' Test setup mask creation '''
        self.assertListEqual(self.service._setup_mask, [False, True, True, True])

        self.service._setup['multiperf'] = "0p 0i 0d"
        self.service._setup['multicfg'] = ""
        self.service._create_setup_mask()
        self.assertListEqual(self.service._setup_mask, [False, False, False])

        self.service._setup['multiperf'] = "MBA1 MBA2 MBA3 MBA4"
        self.service._setup['multicfg'] = "-"
        self.service._create_setup_mask()
        self.assertListEqual(self.service._setup_mask, [False, False, False, False])

        del self.service._setup['multiperf']
        del self.service._setup['multicfg']
        self.service._create_setup_mask()
        self.assertListEqual(self.service._setup_mask, [])

        self.service._setup['multicfg'] = ""
        self.service._create_setup_mask()
        self.assertListEqual(self.service._setup_mask, [])

        del self.service._setup['multicfg']
        self.service._setup['multiperf'] = ""
        self.service._create_setup_mask()
        self.assertListEqual(self.service._setup_mask, [])

        self.service._setup['multiperf'] = "21Sdo 21Sint 21Scal 21Sext"
        self.service._setup['multicfg'] = "4"
        self.service._create_setup_mask()
        self.assertListEqual(self.service._setup_mask, [False, False, False, True])

        self.service._setup['multiperf'] = "HP HPlo HPhi"
        self.service._setup['multicfg'] = "2 3"
        self.service._create_setup_mask()
        self.assertListEqual(self.service._setup_mask, [False, True, True])

        self.service._setup['multiperf'] = "kPx100 kIx1000 kD"
        self.service._setup['multicfg'] = "1 2 3"
        self.service._create_setup_mask()
        self.assertListEqual(self.service._setup_mask, [True, True, True])
