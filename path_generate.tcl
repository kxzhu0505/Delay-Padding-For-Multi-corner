# 读取库文件和网表
read_liberty /home/wllpro/llwang07/kxzhu/DelayPadding/platform/asap7sc7p5t_SIMPLE_RVT_SS_nldm_211120.lib
read_verilog /home/wllpro/llwang07/kxzhu/ssta/distribution/vlsi/gcd/gcd.v

# 链接设计
link_design gcd

# 获取所有时钟
set clock_ports [get_ports "*clk*"]

# 创建时钟和约束
if {$clock_ports != ""} {
    create_clock -name clk -period 10 $clock_ports
}

# 生成setup time(max delay)报告
# set_operating_conditions max
report_checks -path_delay max -group_count 10000   -path_group clk -sort_by_slack > /home/wllpro/llwang07/kxzhu/DelayPadding/path_max.rpt

# 生成hold time(min delay)报告
# set_operating_conditions min
report_checks -path_delay min -group_count 10000  -path_group clk -sort_by_slack > /home/wllpro/llwang07/kxzhu/DelayPadding/path_min.rpt
