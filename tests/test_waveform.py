import csv
import json

import pytest

from rigol_cli.errors import ProtocolError
from rigol_cli.waveform import Waveform, parse_ieee_block, write_waveform


def test_parse_ieee_definite_length_block_and_plain_payload():
    assert parse_ieee_block(b"#9000000004abcd\n") == b"abcd"
    assert parse_ieee_block(b"abc\n") == b"abc"


def test_parse_ieee_block_rejects_truncation():
    with pytest.raises(ProtocolError, match="truncated waveform"):
        parse_ieee_block(b"#14abc")


def test_ds1000e_voltage_and_time_conversion():
    waveform = Waveform("CHANnel1", bytes((125, 100)), 0.001, 0.0, 1.0, 0.0, 1e6)
    assert waveform.voltage_at(0) == 0.0
    assert waveform.voltage_at(1) == 1.0
    assert waveform.time_at(0) == pytest.approx(-0.006)
    assert waveform.time_at(1) == pytest.approx(0.0)


def test_write_waveform_csv_json_and_bin(tmp_path):
    waveform = Waveform("CHANnel1", bytes((125, 100)), 0.001, 0.0, 1.0, 0.0, 1e6)
    csv_path = tmp_path / "capture.csv"
    write_waveform(waveform, csv_path, "csv")
    with csv_path.open() as stream:
        rows = list(csv.reader(stream))
    assert rows[0] == ["index", "time_seconds", "raw", "volts"]
    assert rows[2][-1] == "1.0"
    json_path = tmp_path / "capture.json"
    write_waveform(waveform, json_path, "json")
    assert json.loads(json_path.read_text())["points"] == 2
    bin_path = tmp_path / "capture.bin"
    write_waveform(waveform, bin_path, "bin")
    assert bin_path.read_bytes() == bytes((125, 100))
