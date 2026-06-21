/*
 * Copyright (c) 2024 Danny Rosen
 * SPDX-License-Identifier: Apache-2.0
 *
 * Leaky Integrate-and-Fire (LIF) neuron.
 *
 * Each clock cycle the membrane potential integrates the input current,
 * leaks a fixed amount toward zero, and emits a spike (resetting the
 * potential) once it crosses the firing threshold.
 *
 *   I/O map
 *     ui_in        : input current (synaptic drive), unsigned 8-bit
 *     uo_out[0]    : spike output (1 for one cycle when the neuron fires)
 *     uo_out[7:1]  : 0
 *     uio_out[7:0] : current membrane potential (debug / observability)
 *     uio_in       : unused
 */

`default_nettype none

module tt_um_ex_drosen766 (
    input  wire [7:0] ui_in,    // Dedicated inputs  - input current
    output wire [7:0] uo_out,   // Dedicated outputs - spike on bit 0
    input  wire [7:0] uio_in,   // IOs: Input path   - unused
    output wire [7:0] uio_out,  // IOs: Output path  - membrane potential (debug)
    output wire [7:0] uio_oe,   // IOs: Enable path (active high: 0=input, 1=output)
    input  wire       ena,      // always 1 when the design is powered, so you can ignore it
    input  wire       clk,      // clock
    input  wire       rst_n     // reset_n - low to reset
);

  // LIF parameters (membrane is unsigned, saturates at [0, 255]).
  localparam [7:0] THRESHOLD = 8'd128;  // fire when membrane reaches this
  localparam [7:0] LEAK      = 8'd1;    // leak per cycle toward 0
  localparam [7:0] V_RESET   = 8'd0;    // membrane value after a spike

  reg [7:0] membrane;  // membrane potential (internal state)
  reg       spike;     // 1 for the cycle in which the neuron fires

  // Integrate input current with saturating (no-wrap) addition.
  wire [8:0] integrated = {1'b0, membrane} + {1'b0, ui_in};
  wire [7:0] charged    = integrated[8] ? 8'd255 : integrated[7:0];

  // Apply the leak, flooring at zero.
  wire [7:0] leaked = (charged > LEAK) ? (charged - LEAK) : 8'd0;

  // Fire when the leaked potential reaches threshold.
  wire fire = (leaked >= THRESHOLD);

  always @(posedge clk) begin
    if (!rst_n) begin
      membrane <= V_RESET;
      spike    <= 1'b0;
    end else begin
      spike    <= fire;
      membrane <= fire ? V_RESET : leaked;
    end
  end

  assign uo_out  = {7'b0, spike};
  assign uio_out = membrane;
  assign uio_oe  = 8'hFF;  // membrane potential is driven out on the uio bus

  // List all unused inputs to prevent warnings
  wire _unused = &{ena, uio_in, 1'b0};

endmodule
