# 读取库文件和网表
read_liberty /home/wllpro/llwang07/kxzhu/DelayPadding/platform/asap7sc7p5t_AO_RVT_TT_nldm_211120.lib
read_liberty /home/wllpro/llwang07/kxzhu/DelayPadding/platform/asap7sc7p5t_INVBUF_RVT_TT_nldm_220122.lib
read_liberty /home/wllpro/llwang07/kxzhu/DelayPadding/platform/asap7sc7p5t_OA_RVT_TT_nldm_211120.lib
read_liberty /home/wllpro/llwang07/kxzhu/DelayPadding/platform/asap7sc7p5t_SEQ_RVT_TT_nldm_220123.lib
read_liberty /home/wllpro/llwang07/kxzhu/DelayPadding/platform/asap7sc7p5t_SIMPLE_RVT_TT_nldm_211120.lib
read_verilog /home/wllpro/llwang07/kxzhu/ssta/distribution/vlsi/tv80/tv80.v

# 链接设计
link_design tv80

# 获取所有时钟
set clock_ports [get_ports "*clk*"]

# 创建时钟和约束
if {$clock_ports != ""} {
    create_clock -name clk -period 10 $clock_ports
}

# 生成setup time(max delay)报告
# set_operating_conditions max
report_checks -from _10775_ -to _10891_ -path_delay max 