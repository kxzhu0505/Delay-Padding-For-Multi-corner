# 读取库文件和网表
read_liberty /home/wllpro/llwang07/kxzhu/DelayPadding/platform/asap7sc7p5t_AO_RVT_SS_nldm_211120.lib
read_liberty /home/wllpro/llwang07/kxzhu/DelayPadding/platform/asap7sc7p5t_INVBUF_RVT_SS_nldm_220122.lib
read_liberty /home/wllpro/llwang07/kxzhu/DelayPadding/platform/asap7sc7p5t_OA_RVT_SS_nldm_211120.lib
read_liberty /home/wllpro/llwang07/kxzhu/DelayPadding/platform/asap7sc7p5t_SEQ_RVT_SS_nldm_220123.lib
read_liberty /home/wllpro/llwang07/kxzhu/DelayPadding/platform/asap7sc7p5t_SIMPLE_RVT_SS_nldm_211120.lib
read_verilog /home/wllpro/llwang07/kxzhu/ssta/distribution/vlsi/tv80/tv80.v

# 链接设计
link_design tv80

# 获取所有时钟
set clock_ports [get_ports "*clk*"]

# 创建时钟和约束
if {$clock_ports != ""} {
    create_clock -name clk -period 10 $clock_ports
}

report_checks -from _10597_ -to _10780_ -path_delay max -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/tv80_dir/timing_ss_asap7_max.rpt
report_checks -from _10597_ -to _10777_ -path_delay max -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/tv80_dir/timing_ss_asap7_max.rpt
report_checks -from _10597_ -to _10774_ -path_delay max -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/tv80_dir/timing_ss_asap7_max.rpt
report_checks -from _10775_ -to _10892_ -path_delay max -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/tv80_dir/timing_ss_asap7_max.rpt
report_checks -from _10597_ -to _10778_ -path_delay max -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/tv80_dir/timing_ss_asap7_max.rpt
report_checks -from _10677_ -to _10677_ -path_delay max -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/tv80_dir/timing_ss_asap7_max.rpt
report_checks -from _10779_ -to _10597_ -path_delay max -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/tv80_dir/timing_ss_asap7_max.rpt
report_checks -from _10597_ -to _10781_ -path_delay max -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/tv80_dir/timing_ss_asap7_max.rpt
report_checks -from _10623_ -to _10623_ -path_delay max -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/tv80_dir/timing_ss_asap7_max.rpt
report_checks -from _10775_ -to _10638_ -path_delay max -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/tv80_dir/timing_ss_asap7_max.rpt
report_checks -from _10597_ -to _10779_ -path_delay max -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/tv80_dir/timing_ss_asap7_max.rpt
report_checks -from _10775_ -to _10794_ -path_delay max -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/tv80_dir/timing_ss_asap7_max.rpt
report_checks -from _10621_ -to _10621_ -path_delay max -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/tv80_dir/timing_ss_asap7_max.rpt
report_checks -from _10597_ -to _10775_ -path_delay max -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/tv80_dir/timing_ss_asap7_max.rpt


report_checks -from _10597_ -to _10780_ -path_delay min -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/tv80_dir/timing_ss_asap7_min.rpt
report_checks -from _10597_ -to _10777_ -path_delay min -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/tv80_dir/timing_ss_asap7_min.rpt
report_checks -from _10597_ -to _10774_ -path_delay min -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/tv80_dir/timing_ss_asap7_min.rpt
report_checks -from _10775_ -to _10892_ -path_delay min -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/tv80_dir/timing_ss_asap7_min.rpt
report_checks -from _10597_ -to _10778_ -path_delay min -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/tv80_dir/timing_ss_asap7_min.rpt
report_checks -from _10677_ -to _10677_ -path_delay min -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/tv80_dir/timing_ss_asap7_min.rpt
report_checks -from _10779_ -to _10597_ -path_delay min -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/tv80_dir/timing_ss_asap7_min.rpt
report_checks -from _10597_ -to _10781_ -path_delay min -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/tv80_dir/timing_ss_asap7_min.rpt
report_checks -from _10623_ -to _10623_ -path_delay min -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/tv80_dir/timing_ss_asap7_min.rpt
report_checks -from _10775_ -to _10638_ -path_delay min -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/tv80_dir/timing_ss_asap7_min.rpt
report_checks -from _10597_ -to _10779_ -path_delay min -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/tv80_dir/timing_ss_asap7_min.rpt
report_checks -from _10775_ -to _10794_ -path_delay min -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/tv80_dir/timing_ss_asap7_min.rpt
report_checks -from _10621_ -to _10621_ -path_delay min -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/tv80_dir/timing_ss_asap7_min.rpt
report_checks -from _10597_ -to _10775_ -path_delay min -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/tv80_dir/timing_ss_asap7_min.rpt
