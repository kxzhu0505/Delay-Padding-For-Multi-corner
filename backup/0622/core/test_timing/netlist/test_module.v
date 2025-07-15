
module test_module (
    input wire clk,
    input wire [3:0] in_data,
    output reg [3:0] out_data
);

reg [3:0] stage1, stage2;

always @(posedge clk) begin
    stage1 <= in_data;
    stage2 <= stage1;
    out_data <= stage2;
end

endmodule
