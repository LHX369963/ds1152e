import errno

import pytest

from rigol_cli.errors import TransportError
from rigol_cli.transport import LinuxUsbtmc


def test_encode_adds_exactly_one_line_terminator():
    assert LinuxUsbtmc._encode(":RUN") == b":RUN\n"
    assert LinuxUsbtmc._encode(b"*IDN?\r\n") == b"*IDN?\n"


def test_encode_rejects_embedded_newline():
    with pytest.raises(TransportError, match="embedded newlines"):
        LinuxUsbtmc._encode(":RUN\n:STOP")
