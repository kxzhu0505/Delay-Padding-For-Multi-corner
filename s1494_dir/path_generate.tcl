
# 读取库文件和网表
read_liberty /home/wllpro/llwang07/kxzhu/ssta/distribution/benchmark/s1494/s1494_Early.lib
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
report_checks -path_delay max -unconstrained -format full_clock_expanded > path_max.rpt

# 生成hold time(min delay)报告
# set_operating_conditions min
report_checks -path_delay min -unconstrained -format full_clock_expanded > path_min.rpt
