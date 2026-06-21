# SPDX-License-Identifier: Apache-2.0
# Drives 0b10101010 (0xAA = 170) onto each input wire and checks the output.

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles


@cocotb.test()
async def test_drive_aa(dut):
    PATTERN = 0b10101010  # 0xAA = 170

    # Start a 100 kHz clock
    cocotb.start_soon(Clock(dut.clk, 10, unit="us").start())

    # Reset
    dut.ena.value = 1
    dut.ui_in.value = 0
    dut.uio_in.value = 0
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 2)
    dut.rst_n.value = 1

    # Drive 0b10101010 onto BOTH input wires
    dut.ui_in.value = PATTERN
    dut.uio_in.value = PATTERN
    await ClockCycles(dut.clk, 1)

    # Read back and report
    ui = int(dut.ui_in.value)
    uio = int(dut.uio_in.value)
    out = int(dut.uo_out.value)
    dut._log.info(f"ui_in=0b{ui:08b} ({ui})  uio_in=0b{uio:08b} ({uio})")
    dut._log.info(f"uo_out=0b{out:08b} ({out})")

    # Design is uo_out = ui_in + uio_in, truncated to 8 bits.
    expected = (PATTERN + PATTERN) & 0xFF  # 170 + 170 = 340 -> wraps to 84
    assert out == expected, f"expected {expected} (0b{expected:08b}), got {out}"
