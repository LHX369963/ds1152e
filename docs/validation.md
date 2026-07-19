# DS1152E Validation

Validation date: 2026-07-19

## Instrument

```text
Rigol Technologies,DS1152E,DS1ET192605874,00.04.01.00.02
/dev/usbtmc2
```

The generator connection used for analog checks was DG1022 CH1 to DS1152E CH1
and DG1022 CH2 to DS1152E CH2.

## Catalog Audit

- 164 merged manual catalog entries
- 156 entries applicable to DS1000E/DS1152E
- 8 DS1000D-only logic entries correctly rejected on DS1152E
- 104 query-capable DS1000E entries
- 160 allowed query instances after expanding channels, trigger modes, and
  measurement sources
- 160/160 allowed instances returned a response on the instrument

An initial unconstrained expansion found 14 invalid trigger-mode combinations.
The programming guide confirms those paths do not exist. `CommandSpec.modes` now
models each command's allowed modes, and the CLI rejects unsupported combinations
before opening the instrument.

Query-set original-value writeback covered 112 expanded instances. 106 round
tripped the instrument response verbatim. Six require the guide's input spelling
instead of the display response: sensitivity values need ordinary decimal notation,
and pattern query output must be reduced to its settable value/mask fields. Those
paths were written with valid normalized values and restored.

Action dispatch, confirmation gating for reset/factory load, arbitrary raw SCPI,
and batch dispatch are covered by unit tests or live command use. `HARDcopy` needs
a USB storage device in the scope's host port to prove creation of the bitmap; no
such storage device was part of this setup, so only command availability is claimed.

## Waveform Calibration

The analog conversion was checked with five DC levels from the DG1022. The correct
DS1000E conversion reference is byte 125:

```text
volts = (125 - raw) * scale / 25 - offset
```

At a -1 V generator level, the scope automatic average was -1.02 V and exported
CSV mean was -1.023 V. With 0 V input and +0.5 V scope vertical offset, exported
samples reconstructed approximately -5 mV.

Waveform download restores the original points mode. The final points mode after
validation was `MAXIMUM`.

## Detailed Connected Acceptance

The connected suite in the adjacent DG1022 repository uses the installed `rigol`
entry point for configuration and the fixed DG CH1 -> DS CH1 / DG CH2 -> DS CH2
wiring for observation. Current machine-readable reports cover:

- 136 core cases for acquisition types/modes/averaging, memory depth, NORMAL,
  MAXIMUM and RAW transfers, both channels, DC/AC/GND coupling, channel switches,
  probe factors, scale/offset grids, all 20 automatic measurements, and 18
  CLI waveform export combinations
- 102 trigger/math cases covering EDGE, PULSE, SLOPE, PATTERN, DURATION, VIDEO,
  ALTERNATION, coupling and holdoff settings, A+B/A-B/AB, and three FFT inputs
- 33 shared robustness cases for repeated sessions, exponent/fixed numeric forms,
  invalid input rejection, and batch write/query operation

This work found three CLI compatibility issues. Writes now wait 50 ms by default,
scientific-notation values are converted to fixed decimal for the DS1152E parser,
and `EQUAL_TIME` is sent using the `ETIM` spelling accepted by this firmware.
Negative trigger enums such as `-GREaterthan` are protected from argparse.

The programming guide's `ACQuire:MODE ROLL` value is ignored by this DS1152E
firmware even at 500 ms/div and slower; direct long and abbreviated spellings were
tested. The CLI sends the documented command but does not claim that the instrument
entered Roll. VIDEO, PATTERN, and DURATION settings were exhaustively read back,
but their physical trigger conditions cannot be produced by the fixed two analog
generator connections. MATH/FFT exports are validated as raw display bytes because
the programming interface exposes no math vertical calibration or FFT frequency-axis
metadata.

## Final Connected Baseline

```text
DG CH1 -> DS CH1: 1.000 kHz, 2.04 Vpp
DG CH2 -> DS CH2: 1.980 kHz, 2.02 Vpp
DS channels: display ON, DC, probe 1X, 0.5 V/div, offset 0 V
DS invert: OFF/OFF
DS bandwidth limit: OFF/OFF
DS timebase: 200 us/div
```

Unit test result: 20 passed.
