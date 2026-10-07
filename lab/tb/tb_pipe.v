// =============================================================================
// tb_pipe.v — Testbench / "regression" for pipe.v
// =============================================================================
//
// This file is NOT synthesizable chip RTL. It drives clocks/resets, applies
// stimulus, logs a CSV the Python harness compares, and dumps a VCD waveform.
//
// Plusarg  +stim=<n>  selects how hard the regression exercises the DUT:
//   0  full    allow=1, observe=1  — site can run and the pin can show it
//   1  blind   allow=1, observe=0  — site runs; checked pin forced to 0
//   2  starve  allow=0, observe=1  — site never receives enable
//
// Outputs are written in the directory where `vvp` is launched:
//   trace.csv  — time-series for automated labeling
//   wave.vcd   — open with GTKWave

`timescale 1ns/1ps

module tb_pipe;
  reg        clk = 1'b0;
  reg        rst_n = 1'b0;
  reg        req_en = 1'b0;
  reg        allow = 1'b0;
  reg        observe = 1'b0;
  wire [3:0] count;
  wire [3:0] seen;
  wire       hit;

  integer stim;
  integer fd;

  // Device under test
  pipe dut (
    .clk(clk),
    .rst_n(rst_n),
    .req_en(req_en),
    .allow(allow),
    .observe(observe),
    .count(count),
    .seen(seen),
    .hit(hit)
  );

  // 100 MHz-ish toggle: period = 10 time units
  always #5 clk = ~clk;

  initial begin
    stim = 0;
    if (!$value$plusargs("stim=%d", stim))
      stim = 0;

    fd = $fopen("trace.csv", "w");
    if (fd == 0) begin
      $display("ERROR: could not open trace.csv");
      $finish;
    end
    $fdisplay(fd, "time,count,seen,hit");

    $dumpfile("wave.vcd");
    $dumpvars(0, tb_pipe);

    // Hold reset for a couple of clocks, release on a negedge so the next
    // posedge sees a clean rst_n=1.
    repeat (2) @(posedge clk);
    @(negedge clk);
    rst_n = 1'b1;

    case (stim)
      0: begin allow = 1'b1; observe = 1'b1; end
      1: begin allow = 1'b1; observe = 1'b0; end
      2: begin allow = 1'b0; observe = 1'b1; end
      default: begin
        $display("ERROR: unknown stim %0d", stim);
        $finish;
      end
    endcase

    // Four enabled beats, then idle one cycle for a final sample.
    req_en = 1'b1;
    repeat (4) @(posedge clk);
    @(negedge clk);
    req_en = 1'b0;
    @(posedge clk);
    #2;
    $fclose(fd);
    $finish;
  end

  // Sample AFTER nonblocking (<=) updates have taken effect this cycle.
  always @(posedge clk) begin
    if (rst_n) begin
      #1 $fdisplay(fd, "%0t,%0d,%0d,%0d", $time, count, seen, hit);
    end
  end
endmodule
