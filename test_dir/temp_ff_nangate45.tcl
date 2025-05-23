
# 读取库文件和网表
read_liberty /home/wllpro/llwang07/kxzhu/ssta/OpenSTA_D/examples/nangate45_fast.lib
read_verilog /home/wllpro/llwang07/kxzhu/ssta/OpenSTA_D/examples/example1.v

# 链接设计
link_design top

# 获取所有时钟
set clock_ports [get_ports "*clk*"]

# 创建时钟和约束
if {$clock_ports != ""} {
    create_clock -name clk -period 10 $clock_ports
}

# 生成setup time(max delay)报告
# set_operating_conditions max
report_checks -from r2 -to r3 -path_delay max -format full_clock_expanded >> timing_ff_nangate45_max.rpt
report_checks -from r1 -to r3 -path_delay max -format full_clock_expanded >> timing_ff_nangate45_max.rpt

# 生成hold time(min delay)报告
# set_operating_conditions min
report_checks -from r2 -to r3 -path_delay min -format full_clock_expanded >> timing_ff_nangate45_min.rpt
report_checks -from r1 -to r3 -path_delay min -format full_clock_expanded >> timing_ff_nangate45_min.rpt
"""