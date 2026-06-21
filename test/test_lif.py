# SPDX-License-Identifier: Apache-2.0
# Tests for the Leaky Integrate-and-Fire (LIF) neuron in src/project.v.

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, RisingEdge, Timer

# Must match the localparams in src/project.v
THRESHOLD = 128
LEAK = 1
V_RESET = 0


async def reset(dut):
    cocotb.start_soon(Clock(dut.clk, 10, unit="us").start())
    dut.ena.value = 1
    dut.ui_in.value = 0
    dut.uio_in.value = 0
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 3)
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")  # let combinational outputs settle


def membrane(dut):
    return int(dut.uio_out.value)


def spike(dut):
    return int(dut.uo_out.value) & 1


@cocotb.test()
async def test_reset(dut):
    """After reset the membrane is cleared and no spike is emitted."""
    await reset(dut)
    assert membrane(dut) == V_RESET, f"membrane={membrane(dut)} after reset"
    assert spike(dut) == 0, "spike asserted after reset"


@cocotb.test()
async def test_integration_and_leak(dut):
    """With no input the membrane should not change from reset; with a
    sub-threshold drive it integrates then leaks back down."""
    await reset(dut)

    # Drive a constant sub-threshold current and watch it ramp up by
    # (current - LEAK) each cycle, never spiking.
    current = 20
    dut.ui_in.value = current
    expected = V_RESET
    for _ in range(5):
        await RisingEdge(dut.clk)
        await Timer(1, unit="ns")
        charged = min(expected + current, 255)
        expected = max(charged - LEAK, 0)
        if expected >= THRESHOLD:
            expected = V_RESET  # would have spiked; not expected here
        assert membrane(dut) == expected, (
            f"membrane={membrane(dut)} expected={expected}"
        )
        assert spike(dut) == 0, "unexpected spike below threshold"

    # Remove the drive: membrane should leak back toward zero.
    dut.ui_in.value = 0
    prev = membrane(dut)
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    assert membrane(dut) == max(prev - LEAK, 0), "membrane did not leak down"


@cocotb.test()
async def test_fires_and_resets(dut):
    """A strong input pushes the neuron over threshold; it must emit a
    single-cycle spike and reset the membrane."""
    await reset(dut)

    dut.ui_in.value = THRESHOLD + 10  # guaranteed supra-threshold in one step
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    assert spike(dut) == 1, "neuron did not fire on supra-threshold input"
    assert membrane(dut) == V_RESET, "membrane not reset after firing"

    # Drop the input; the spike must not persist.
    dut.ui_in.value = 0
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    assert spike(dut) == 0, "spike persisted longer than one cycle"


@cocotb.test()
async def test_periodic_firing(dut):
    """A sustained supra-threshold-rate input produces repeated spikes."""
    await reset(dut)
    dut.ui_in.value = 64  # reaches threshold every few cycles

    spikes = 0
    for _ in range(40):
        await RisingEdge(dut.clk)
        await Timer(1, unit="ns")
        spikes += spike(dut)

    assert spikes >= 2, f"expected repeated firing, saw {spikes} spikes"
