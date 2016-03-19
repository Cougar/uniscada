"""Service Description Protocol.

Message datagram composition and decomposition
according to the Uniscada Service Description Protocol.
"""
import re
import copy

from sdpitem import SDPItem
from sdpexception import SDPException, SDPDecodeException

import logging
log = logging.getLogger(__name__)   # pylint: disable=invalid-name
log.addHandler(logging.NullHandler())

class UnsecureSDP(SDPItem):
    """ Convert to and from SDP protocol datagram """

    def __init__(self, secret_key=None, nonce=None):
        """ Create a new empty in-memory ``SDP`` datagram
        """
        super(UnsecureSDP, self).__init__()
        self._multipart_pieces = []
        self._multipart_parent = None

    def _empty_sdp(self):
        """ Clear all data from this SDP instance
        """
        super(UnsecureSDP, self)._empty_sdp()
        self._multipart_pieces = []
        self._multipart_parent = None

    def add_keyvalue(self, key, val):
        """ Add key:val pair to the packet

        * if val is "?", it is saved as a special query
        * if key ends with "F", it is saved as a Float (hex str)
          also TOV as legacy!
        * if key ends with "S", it is saved as a Status
          (int [0 .. 3] or str ['0' .. '3'])
        * if key ends with "V", it is saved as a Value (int, float or str)
        * if key ends with "W", it is saved as a List of Values (str)
        * all other keys are saved as Data (str)

        String 'null' is allowed in "V" and "W" keys and will be changed
        to None

        Data type conversion is caller responsibility. Only valid
        data types are accepted.

        :param key: data key
        :param val: data value
        """
        if len(self._multipart_pieces) and key != 'id':
                raise SDPException('only "id" can be added to multipart parent')
        if self._multipart_parent and key == 'id':
            parent_id = self._multipart_parent.get_data('id')
            if not parent_id:
                raise SDPException('parent SDP "id" is missing')
            if parent_id != val:
                raise SDPException('parent SDP "id" is different')
            return
        super(UnsecureSDP, self).add_keyvalue(key, val)

    def get_data(self, key):    # pylint: disable=too-many-return-statements
        """ Get value of saved data

        :param key: data key

        * If key ends with "S", it returns a Status (int)
        * Hex float keys end with "F" (or key is "TOV"),
          returns hex float string
        * If key ends with "V", it returns a Value (int, float or str)
        * If key ends with "W", it returns a List of Values (list)
        * All other keys returns a Data (str)

        :returns: Status, Value, List of Values, Data or
        None if key is missing
        """
        if key == 'id' and self._multipart_parent:
            return self._multipart_parent.data.get('id', None)
        return super(UnsecureSDP, self).get_data(key)

    def add_sdp_multipart(self, sdp):
        """ Add data from SDP to multipart SDP

        :param sdp: simple SDP with timestamp
        """
        if self == sdp:
            raise SDPException('cant add SDP to itself')
        if not isinstance(sdp, SDPItem) and len(sdp._multipart_pieces):
            raise SDPException('multipart SDP cant be added to another SDP')
        if self._multipart_parent:
            raise SDPException('parent SDP is already part of another multipart SDP')
        if not isinstance(sdp, SDPItem) and sdp._multipart_parent:
            raise SDPException('SDP is already part of another multipart SDP')
        if self.get_timestamp():
            raise SDPException('timestamp is not allowed in parent SDP')
        id = sdp.get_data('id')
        if id:
            parent_id = self.get_data('id')
            if not parent_id:
                raise SDPException('"id" in multipart but not in parent SDP')
            if parent_id != id:
                raise SDPException('"id" in multipart must be equal with "id" in parent SDP')
            sdp.remove_data('id')
        ts = sdp.get_timestamp()
        if not ts:
            raise SDPException('timestamp is required for multipart SDP')
        if len(self._multipart_pieces):
            if ts <= self._multipart_pieces[-1].get_timestamp():
                raise SDPException('timestamp is not growing')
        else:
            for (key, val) in self.get_data_list():
                if key != 'id':
                    raise SDPException('other keys than "id" is not allowed in parent SDP: %s' % key)
        sdp.remove_data('id')
        self._multipart_pieces.append(sdp)
        sdp._multipart_parent = self

    def remove_sdp_multipart(self, sdp):
        """ Remove one part from multipart SDP

        :param sdp: part instance in multipart SDP
        """
        self._multipart_pieces.remove(sdp)

    def get_multipart_list(self):
        """ Generates list or all SDP pieces in multipart SDP

        :yields: SDP piece
        """
        for sdp in self._multipart_pieces:
            yield sdp

    def encode(self, controllerid=None):
        """ Encodes SDP packet to datagram

        :param controllerid: Optional paramater for id:<val> Data (str)

        :returns: The string representation of SDP datagram
        """
        datagram = super(UnsecureSDP, self).encode(controllerid)
        for sdp in self._multipart_pieces:
            datagram += sdp._encode_data()
        return datagram

    @staticmethod
    def decode(datagram, sdp=None):
        """ Decodes SDP datagram to packet

        :param datagram: The string representation of SDP datagram
        """

        log.debug("decode")
        controllerid = None
        multipart_parent = None
        if not sdp:
            sdp = SDPItem()
        for line in datagram.splitlines():
            if line == '':
                log.warning('empty line in datagram')
                continue
            (key, val) = SDPItem._decode_line(line)
            if key == 'id':
                if controllerid:
                    raise SDPDecodeException('ONLY ONE "id" is allowed')
                controllerid = val
            if sdp.get_data(key):
                if key == "in":
                    if not multipart_parent:
                        if not controllerid:
                            raise SDPDecodeException('in multipart SDP the "id" MUST BE before first "in"')
                        multipart_parent = UnsecureSDP()
                        multipart_parent.add_keyvalue("id", controllerid)
                    multipart_parent.add_sdp_multipart(sdp)
                    sdp = SDPItem()
                else:
                    raise SDPDecodeException('multiple "%s" fields' % key)
            try:
                sdp.add_keyvalue(key, val)
            except SDPException as ex:
                raise SDPDecodeException(ex)
        if not controllerid:
            log.error('"id" missing in datagram')
            raise SDPDecodeException('"id:" _MUST_ exists in datagram')
        if multipart_parent:
            multipart_parent.add_sdp_multipart(sdp)
            return multipart_parent
        else:
            return sdp

    def __add__(self, val):
        """ Add (key, value) tuple to the SDP or
        add another SDP instance to the multipart SDP

        CAUTION! first summand will be changed and returned
        """
        if isinstance(val, tuple):
            self.add_keyvalue(val[0], val[1])
            return self
        if isinstance(val, UnsecureSDP):
            self.add_sdp_multipart(val)
            return self
        return super(UnsecureSDP, self).__add__(val)

    def __str__(self):
        """ Returns data dictionary """
        s = ""
        if self._multipart_parent:
            s = s + "(child) "
        s = s + super(UnsecureSDP, self).__str__() + "\n"
        if self._multipart_pieces:
            for piece in self._multipart_pieces:
                s = s + " \\ " + str(piece)
        return s
