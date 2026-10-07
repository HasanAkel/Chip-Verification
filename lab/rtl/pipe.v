// =============================================================================
// pipe.v — Tiny DUT that makes three masking outcomes visible in a waveform.
// =============================================================================
//
// Data path (left = inputs, right = what a scoreboard would check):
//
//   allow, req_en --> upstream AND gate --> counter --> observe mux --> seen
//
// Bug site: the counter's "+ 1" (toggle with `+define+BUG_SUB` at compile time).
//
// Masking knobs (same idea as real SoC interconnects / muxes / enables):
//   BUG_ALLOW_STUCK  — upstream enable stuck at 0  → starvation of the site
//   observe == 0     — downstream mux forces seen=0 → cover-up of local error
//
// Probes (not typical chip pins; lab-only so we can label mask type):
//   count — local state at the bug site
//   hit   — 1 after the site has actually taken an enable pulse
//   seen  — checked output (what a normal testbench would compare)

module pipe (
  input  wire       clk,
  input  wire       rst_n,     // active-low reset
  input  wire       req_en,    // request to advance the counter
  input  wire       allow,     // upstream permission (arbiter / decode stand-in)
  input  wire       observe,   // 1: forward count; 0: force seen to 0
  output reg  [3:0] count,     // local probe at the mutation site
  output wire [3:0] seen,      // pin a checker would watch
  output reg        hit        // local probe: site was enabled at least once
);
  wire allow_i;
  wire en;

  // Upstream gate. Injecting BUG_ALLOW_STUCK models a second bug that
  // prevents req_en from ever reaching the counter.
`ifdef BUG_ALLOW_STUCK
  assign allow_i = 1'b0;
`else
  assign allow_i = allow;
`endif

  assign en = req_en & allow_i;

  // Synchronous counter: the intentional single-site bug lives here.
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      count <= 4'd0;
      hit   <= 1'b0;
    end else if (en) begin
      hit <= 1'b1;
`ifdef BUG_SUB
      // Mutant: decrement instead of increment (ExprUpdate-style edit).
      count <= count - 4'd1;
`else
      count <= count + 4'd1;
`endif
    end
  end

  // Downstream mux: when observe=0, local corruption never reaches "seen".
  assign seen = observe ? count : 4'd0;
endmodule
