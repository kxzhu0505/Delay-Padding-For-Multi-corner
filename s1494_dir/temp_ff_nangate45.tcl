
# 读取库文件和网表
read_liberty /home/wllpro/llwang07/kxzhu/ssta/distribution/benchmark/s1494/s1494_Late.lib
read_verilog /home/wllpro/llwang07/kxzhu/ssta/distribution/benchmark/s1494/s1494.v

# 链接设计
link_design s1494

# 获取所有时钟
set clock_ports [get_ports "*clk*"]

# 创建时钟和约束
if {$clock_ports != ""} {
    create_clock -name clk -period 10 $clock_ports
}

# 生成setup time(max delay)报告
# set_operating_conditions max
report_checks -from inst_762 -to inst_765/D -path_delay max -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/s1494_dir/timing_ff_nangate45_max.rpt
report_checks -from inst_765 -to inst_765 -path_delay max -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/s1494_dir/timing_ff_nangate45_max.rpt

# 生成hold time(min delay)报告
# set_operating_conditions min
report_checks -from inst_762 -to inst_765/D -path_delay min -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/s1494_dir/timing_ff_nangate45_min.rpt
report_checks -from inst_765 -to inst_765 -path_delay min -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/s1494_dir/timing_ff_nangate45_min.rpt
"""