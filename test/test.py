import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, RisingEdge


# Expected 8-step pattern (must match src/project.v pattern table)
EXPECTED_PATTERN = [
    0b000,  # step 0: idle
    0b001,  # step 1: 90 deg pulse
    0b000,  # step 2: delay
    0b010,  # step 3: 180 deg pulse
    0b000,  # step 4: delay
    0b100,  # step 5: readout trigger
    0b000,  # step 6: delay
    0b000,  # step 7: idle
]


@cocotb.test()
async def test_sequence(dut):
    dut._log.info("Start pulse sequencer test")

    # 10 MHz clock -> 100 ns period
    clock = Clock(dut.clk, 100, units="ns")
    cocotb.start_soon(clock.start())

    # Use fastest step rate for simulation speed: ui_in[7:4] = 0
    dut.ui_in.value = 0
    dut.uio_in.value = 0
    dut.ena.value = 1
    dut.rst_n.value = 0

    await ClockCycles(dut.clk, 10)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 5)

    dut._log.info("Checking sequence advances through all 8 steps twice")

    # Sample uo_out right after every 'tick' boundary.
    # With ui_in[7:4]=0, div_max = 0xFFF (4095), so each step takes
    # 4096 clock cycles. We just wait long enough for a full tick
    # and sample the settled value at each step.
    seen_pattern = []
    for i in range(N := len(EXPECTED_PATTERN) * 2):
        # wait for one full step period (div_max+1 cycles)
        await ClockCycles(dut.clk, 4096)
        val = int(dut.uo_out.value) & 0b111
        seen_pattern.append(val)

    dut._log.info(f"Observed pattern: {seen_pattern}")

    # Compare against two repetitions of the expected pattern,
    # allowing for an arbitrary phase offset (since we don't know
    # exactly which step we synced to first).
    full_expected = (EXPECTED_PATTERN * 3)
    found = False
    for offset in range(len(EXPECTED_PATTERN)):
        candidate = full_expected[offset: offset + len(seen_pattern)]
        if candidate == seen_pattern:
            found = True
            break

    assert found, (
        f"Observed pattern {seen_pattern} does not match expected "
        f"sequence {EXPECTED_PATTERN} at any phase offset"
    )

    dut._log.info("Pulse sequence matched expected pattern")


@cocotb.test()
async def test_reset(dut):
    dut._log.info("Start reset test")

    clock = Clock(dut.clk, 100, units="ns")
    cocotb.start_soon(clock.start())

    dut.ui_in.value = 0
    dut.uio_in.value = 0
    dut.ena.value = 1
    dut.rst_n.value = 0

    await ClockCycles(dut.clk, 10)

    # During reset, output should be idle (step 0 pattern = 0)
    assert int(dut.uo_out.value) & 0b111 == 0b000, "Output not idle during reset"

    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 5)

    dut._log.info("Reset test passed")
