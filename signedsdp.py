"""Service Description Protocol.

Message datagram composition and decomposition
according to the Uniscada Service Description Protocol.
"""
import hmac
import hashlib
import base64

from unsecuresdp import UnsecureSDP
from sdpexception import SDPException, SDPDecodeException

import logging
log = logging.getLogger(__name__)   # pylint: disable=invalid-name
log.addHandler(logging.NullHandler())

class SignedSDP(UnsecureSDP):
    """ Convert to and from signed SDP protocol datagram """
    def __init__(self, secret_key=None, nonce=None):
        """ Create a new empty in-memory ``SDP`` datagram
        """
        super(SignedSDP, self).__init__()
        self._secret_key = secret_key
        self._nonce = nonce
        self._csum = None
        if secret_key:
            self.set_secret_key(secret_key)
        if nonce:
            self.set_nonce(nonce)

    def _empty_sdp(self):
        """ Clear all data from this SDP instance
        """
        super(SignedSDP, self)._empty_sdp()
        self._signed = False

    def set_secret_key(self, secret_key):
        """ Set secret key for HMAC

        :param secret_key: secret key for HMAC
        """
        self._secret_key = secret_key

    def set_nonce(self, nonce):
        """ Set nonce key for HMAC

        :param nonce: nonce for HMAC calculation
        """
        self._nonce = nonce

    def is_signed(self):
        return self._signed

    def _add_keyvalue_string(self, key, val):
        """ Add single value key:val pair to the packet

        :param key: data key
        :param val: data values as string
        """
        if key == 'sha256':
            raise SDPException('"sha256" is not a valid key')
        super(SignedSDP, self)._add_keyvalue_string(key, val)

    def encode(self, controllerid=None):
        """ Encodes SDP packet to datagram

        :param controllerid: Optional paramater for id:<val> Data (str)

        :returns: The string representation of SDP datagram
        """
        datagram = super(SignedSDP, self).encode(controllerid)
        if self._secret_key:
            self.add_signature(datagram)
            datagram += 'sha256:' + self._sha256 + '\n'
        return datagram

    def add_signature(self, datagram):
        """ Add signature to SDP instance based on datagram string

        :param datagram: unsigned SDP datagram
        """
        if self._nonce == None:
            raise SDPDecodeException("nonce is required for HMAC")

        self._csum = SignedSDP._calculate_checksum(datagram)
        self._sha256 = SignedSDP._calculate_signature(self._csum, self._secret_key, self._nonce)
        self._signed = True
        return

    @classmethod
    def decode(cls, datagram, secret_key=None, nonce=None):
        """ Decodes SDP datagram to packet

        :param datagram: The string representation of SDP datagram
        """
        datagram_before_sig = ''
        sha256 = None
        csum = None
        for line in datagram.splitlines():
            if sha256:
                log.error('no data is allowed after signature')
                raise SDPDecodeException('no data is allowed after signature')
            if line == '':
                log.warning('empty line in datagram')
                continue
            (key, val) = SignedSDP._decode_line(line)
            if key == 'sha256':
                sha256 = val
                csum = SignedSDP._calculate_checksum(datagram_before_sig)
                if secret_key:
                    if not SignedSDP._check_signature(csum, sha256, secret_key, nonce):
                        raise SDPDecodeException('signature check error')
                continue
            datagram_before_sig += line + '\n'
        sdp = SignedSDP()
        sdp = UnsecureSDP.decode(datagram_before_sig, sdp)
        if sha256:
            sdp.set_secret_key(secret_key)
            sdp.set_nonce(nonce)
            sdp._sha256 = sha256
            sdp._csum = csum
            sdp._signed = True
        return sdp

    def check_signature(self):
        if not self._signed:
            return False
        if not self._sha256:
            log.warning('SDP signature is not known')
            return False
        if not self._csum:
            log.warning('SDP checksum is not known')
            return False
        return SignedSDP._check_signature(self._csum, self._sha256, self._secret_key, self._nonce)

    @staticmethod
    def _check_signature(checksum, sha256, secret_key=None, nonce=None):
        if not sha256:
            log.warning('SDP is not signed')
            return False
        signature = SignedSDP._calculate_signature(checksum, secret_key, nonce)
        return hmac.compare_digest(sha256, signature)

    @staticmethod
    def _calculate_checksum(datagram):
        """ Return checksum for given datagram

        :param datagram: unsigned datagram

        :returns: BASE64 encoded checksum
        """
        return base64.b64encode(hashlib.sha256(datagram.encode("UTF-8")).digest()).decode()

    @staticmethod
    def _calculate_signature(checksum, secret_key, nonce):
        """ Return signature for given checksum

        :param checksum: checksum
        :param secret_key: secret key
        :param nonce: nonce

        :returns: BASE64 encoded signature
        """
        if not secret_key:
            log.error('secret key is missing')
            raise SDPDecodeException('checksum exists but ' \
                'secret key is missing')
        if nonce == None:
            log.error('nonce is missing')
            raise SDPDecodeException('checksum exists but ' \
                'nonce is missing')
        return base64.b64encode( \
            hmac.new(secret_key.encode("UTF-8"), \
                msg=nonce.encode("UTF-8")+checksum.encode("UTF-8"), \
                digestmod=hashlib.sha256).digest()).decode()

    def __str__(self):
        """ Returns data dictionary """
        s = "signed: \n"
        s = s + super(SignedSDP, self).__str__()
        return s
