"""Service Description Protocol.

Message datagram composition and decomposition
according to the Uniscada Service Description Protocol.
"""
import re

from sdpitem import SDPItem
from sdpexception import SDPException, SDPDecodeException

import logging
log = logging.getLogger(__name__)   # pylint: disable=invalid-name
log.addHandler(logging.NullHandler())

class UnsecureSDP(SDPItem):
    """ Convert to and from SDP protocol datagram """
