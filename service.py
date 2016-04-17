''' Service setup
'''

import logging
log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())

__all__ = [
    'Service',
    'get_id',
    'set_setup', 'get_setup',
    'get_service_data_v1',
]

class Service(object):
    def __init__(self, id, listinstance = None):
        ''' Create new service instance

        :param id: service id (register name)
        :param listinstance: optional Services instance
        '''
        log.debug('Create a new service (%s)', str(id))
        self._id = id
        self._setup = {}
        self._data_v1 = {}
        self._setup_mask = []

    def get_id(self):
        ''' Get id of service

        :returns: id of service
        '''
        return self._id

    def set_setup(self, setup):
        ''' Set setup data

        :param setup: setup data
        '''
        self._setup = setup
        self._create_setup_mask()
        self._create_data_v1()

    def get_setup(self):
        ''' Return setup data

        :returns: setup data
        '''
        return self._setup

    def get_service_data_v1(self):
        ''' Return service data in API v1 format

        :returns: service data in API v1 format
        '''
        return self._data_v1

    def _create_data_v1(self):
        ''' Create service data in API v1 format
        '''
        (show, key) = self._get_show_and_key()
        if not show:
            self._data_v1 = {}
            return
        unit = self._setup.get('out_unit', '')
        desc = [ self._setup.get('desc0', ''), self._setup.get('desc1', ''), self._setup.get('desc2', '') ]
        multiperf = self._setup.get('multiperf')
        if not multiperf:
            multiperf = ''
        multivalue = self._setup.get('multivalue')
        if not multivalue:
            multivalue = ''
        multicfg = self._setup.get('multicfg', '')

        r = {}
        r['svc_name'] = self._setup.get('svc_name', '')
        r['key'] = key
        r['show'] = show
        mperf = multiperf.split(' ')
        mvalue = multivalue.split(' ')
        r['description'] = []
        for dm in range(len(desc)):
            desc_dm = desc[dm]
            description = {}
            description['status'] = dm
            if (len(mvalue) > 0 and len(mperf) > 0):
                if ':' in desc[dm]:
                    for m in range(len(mperf)):
                        if str(m+1) in mvalue:
                            desc_dm = desc_dm + ' {{ ' + mperf[m] + '.val }}' + unit
            description['desc'] = desc_dm
            r['description'].append(description)
        r['multiperf'] = []
        for mp in range(len(mperf)):
            multiperf = {}
            if mperf[mp] == '':
                multiperf['name'] = r['svc_name']
            else:
                multiperf['name'] = mperf[mp]
            multiperf['cfg'] = False
            if (len(multicfg) > 0 and len(mperf) > 0):
                if str(mp+1) in multicfg:
                    multiperf['cfg'] = True
            r['multiperf'].append(multiperf)
        self._data_v1 = r

    def _get_show_and_key(self):
        ''' Return Show and Key values

        :returns: (show, key) tuple or (None, None)
        '''
        sta_reg = self._id
        val_reg = self._setup.get('val_reg', '')
        if ((val_reg[-1:] == 'V' or val_reg[-1:] == 'W') and sta_reg[-1:] =='S'):
            return (True, val_reg)
        elif (val_reg == '' and sta_reg[-1:] == 'S'):
            return (True, sta_reg)
        elif (val_reg != '' and sta_reg == ''):
            return (False, val_reg)
        else:
            return (None, None)

    def _create_setup_mask(self):
        ''' create mask for r/w setup keys
        '''
        self._setup_mask = []
        multicfg = set(self._setup.get('multicfg', "").split())
        for i in range(len(self._setup.get('multiperf', "").split())):
            self._setup_mask.append(str(i+1) in multicfg)

    def __str__(self):
        return(str(self._id) + ': ' +
               'setup = ' + str(self._setup))
