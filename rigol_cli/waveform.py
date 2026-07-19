from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path

from .errors import ProtocolError


@dataclass(frozen=True)
class Waveform:
    source: str
    raw: bytes
    time_scale: float
    time_offset: float
    vertical_scale: float | None
    vertical_offset: float | None
    sample_rate: float | None

    @property
    def point_count(self) -> int:
        return len(self.raw)

    def time_at(self, index: int) -> float:
        if self.point_count == 0:
            return self.time_offset
        return (index - self.point_count / 2) * (12 * self.time_scale / self.point_count) + self.time_offset

    def voltage_at(self, index: int) -> float | None:
        if self.vertical_scale is None or self.vertical_offset is None:
            return None
        return (125 - self.raw[index]) * (self.vertical_scale / 25.0) - self.vertical_offset


def parse_ieee_block(data: bytes) -> bytes:
    data = data.rstrip(b"\r\n")
    if not data.startswith(b"#"):
        return data
    if len(data) < 2 or not chr(data[1]).isdigit():
        raise ProtocolError("malformed IEEE 488.2 block header")
    digits = data[1] - ord("0")
    if digits == 0:
        return data[2:]
    if len(data) < 2 + digits:
        raise ProtocolError("truncated IEEE 488.2 block length")
    try:
        length = int(data[2 : 2 + digits])
    except ValueError as exc:
        raise ProtocolError("invalid IEEE 488.2 block length") from exc
    start = 2 + digits
    end = start + length
    if len(data) < end:
        raise ProtocolError(f"truncated waveform block: expected {length} bytes, received {len(data) - start}")
    return data[start:end]


def write_waveform(waveform: Waveform, output: Path, format_name: str) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    if format_name == "bin":
        output.write_bytes(waveform.raw)
        return
    if format_name == "json":
        payload = {
            "source": waveform.source,
            "points": waveform.point_count,
            "time_scale_seconds": waveform.time_scale,
            "time_offset_seconds": waveform.time_offset,
            "vertical_scale_volts": waveform.vertical_scale,
            "vertical_offset_volts": waveform.vertical_offset,
            "sample_rate_hz": waveform.sample_rate,
            "samples": [
                {
                    "index": index,
                    "time_seconds": waveform.time_at(index),
                    "raw": value,
                    "volts": waveform.voltage_at(index),
                }
                for index, value in enumerate(waveform.raw)
            ],
        }
        output.write_text(json.dumps(payload, indent=2) + "\n")
        return
    if format_name != "csv":
        raise ProtocolError(f"unsupported waveform format {format_name!r}")
    with output.open("w", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(("index", "time_seconds", "raw", "volts"))
        for index, value in enumerate(waveform.raw):
            writer.writerow((index, f"{waveform.time_at(index):.12g}", value, waveform.voltage_at(index)))
