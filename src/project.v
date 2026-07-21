/*
 * NMR Pulse Sequencer - Tiny Tapeout (GF180MCU)
 * 8-step fixed pulse sequence generator.
 *
 * uo_out[0] = 90 deg RF pulse channel
 * uo_out[1] = 180 deg RF pulse channel
 * uo_out[2] = readout / ADC trigger
 * uo_out[7:3] = unused (tied low)
 *
 * ui_in[7:4] = step-rate select (clock divider coarse control)
 * ui_in[3:0] = unused for now
 */

`default_nettype none

module tt_um_ponprapa_nmr_pulse_sequencer (
    input  wire [7:0] ui_in,
    output wire [7:0] uo_out,
    input  wire [7:0] uio_in,
    output wire [7:0] uio_out,
    output wire [7:0] uio_oe,
    input  wire        ena,
    input  wire        clk,
    input  wire        rst_n
);

    // ---------------------------------------------------------
    // 1. Clock divider - produces a single-cycle 'tick' pulse
    //    Divide ratio is set by ui_in[7:4] (4-bit coarse select)
    // ---------------------------------------------------------
    reg  [15:0] div_cnt;
    wire        tick;
    wire [15:0] div_max = {ui_in[7:4], 12'hFFF};

    assign tick = (div_cnt == 16'd0);

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            div_cnt <= 16'd0;
        else if (ena)
            div_cnt <= tick ? div_max : (div_cnt - 16'd1);
    end

    // ---------------------------------------------------------
    // 2. Step counter - cycles through 8 steps (0..7)
    // ---------------------------------------------------------
    localparam N_STEPS = 8;

    reg [2:0] step;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            step <= 3'd0;
        else if (ena && tick)
            step <= (step == N_STEPS - 1) ? 3'd0 : step + 3'd1;
    end

    // ---------------------------------------------------------
    // 3. Pattern table - fixed spin-echo-style sequence
    //    step: 0=idle 1=90deg 2=delay 3=180deg 4=delay
    //          5=readout 6=delay 7=idle
    // ---------------------------------------------------------
    reg [2:0] pattern_out;

    always @(*) begin
        case (step)
            3'd0: pattern_out = 3'b000; // idle
            3'd1: pattern_out = 3'b001; // 90 deg pulse
            3'd2: pattern_out = 3'b000; // delay
            3'd3: pattern_out = 3'b010; // 180 deg pulse
            3'd4: pattern_out = 3'b000; // delay
            3'd5: pattern_out = 3'b100; // readout / ADC trigger
            3'd6: pattern_out = 3'b000; // delay
            3'd7: pattern_out = 3'b000; // idle
            default: pattern_out = 3'b000;
        endcase
    end

    assign uo_out  = {5'b00000, pattern_out};
    assign uio_out = 8'b0;
    assign uio_oe  = 8'b0;

    // List all unused inputs to avoid warnings
    wire _unused = &{ena, uio_in, ui_in[3:0], 1'b0};

endmodule
