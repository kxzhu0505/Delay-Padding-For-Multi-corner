# delay calc example
read_liberty /home/wllpro/llwang07/kxzhu/DelayPadding/platform/asap7sc7p5t_AO_RVT_FF_nldm_211120.lib
read_liberty /home/wllpro/llwang07/kxzhu/DelayPadding/platform/asap7sc7p5t_INVBUF_RVT_FF_nldm_220122.lib
read_liberty /home/wllpro/llwang07/kxzhu/DelayPadding/platform/asap7sc7p5t_OA_RVT_FF_nldm_211120.lib
read_liberty /home/wllpro/llwang07/kxzhu/DelayPadding/platform/asap7sc7p5t_SEQ_RVT_FF_nldm_220123.lib
read_liberty /home/wllpro/llwang07/kxzhu/DelayPadding/platform/asap7sc7p5t_SIMPLE_RVT_FF_nldm_211120.lib

read_verilog /home/wllpro/llwang07/kxzhu/ssta/distribution/vlsi/gcd/gcd.v
link_design gcd
create_clock -name clk -period 10 {clk}
set_input_delay -clock clk 0 {req_val reset}
report_checks -path_delay max -group_count 10000 -path_group clk -sort_by_slack > /home/wllpro/llwang07/kxzhu/DelayPadding/gcd_dir/ff.rpt
