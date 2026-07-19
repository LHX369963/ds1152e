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


def test_negative_command_delay_is_rejected():
    device = type("Device", (), {})()
    with pytest.raises(TransportError, match="cannot be negative"):
        LinuxUsbtmc(device, command_delay_ms=-1)


def test_write_waits_for_instrument_processing(monkeypatch):
    device = type("Device", (), {})()
    transport = LinuxUsbtmc(device, command_delay_ms=50)
    transport._fd = 7
    sleeps = []
    monkeypatch.setattr("rigol_cli.transport.os.write", lambda fd, payload: len(payload))
    monkeypatch.setattr("rigol_cli.transport.time.sleep", sleeps.append)
    assert transport.write(":RUN") == 5
    assert sleeps == [0.05]
