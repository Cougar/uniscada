"""Service Description Protocol.

Message datagram composition and decomposition
according to the Uniscada Service Description Protocol.
"""
from signedsdp import SignedSDP

import logging
log = logging.getLogger(__name__)   # pylint: disable=invalid-name
log.addHandler(logging.NullHandler())

class SDP(SignedSDP):
    """ This is a wrapper class for a real SDP class (SignedSDP) """
