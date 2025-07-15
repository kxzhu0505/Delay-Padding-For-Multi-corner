# 读取库文件和网表
read_liberty /home/wllpro/llwang07/kxzhu/DelayPadding/platform/asap7sc7p5t_AO_RVT_FF_nldm_211120.lib
read_liberty /home/wllpro/llwang07/kxzhu/DelayPadding/platform/asap7sc7p5t_INVBUF_RVT_FF_nldm_220122.lib
read_liberty /home/wllpro/llwang07/kxzhu/DelayPadding/platform/asap7sc7p5t_OA_RVT_FF_nldm_211120.lib
read_liberty /home/wllpro/llwang07/kxzhu/DelayPadding/platform/asap7sc7p5t_SEQ_RVT_FF_nldm_220123.lib
read_liberty /home/wllpro/llwang07/kxzhu/DelayPadding/platform/asap7sc7p5t_SIMPLE_RVT_FF_nldm_211120.lib
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
report_checks -from _594_ -to _618_ -path_delay max -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/gcd_dir/timing_ff_asap7_max.rpt
report_checks -from _594_ -to _617_ -path_delay max -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/gcd_dir/timing_ff_asap7_max.rpt
report_checks -from _594_ -to _614_ -path_delay max -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/gcd_dir/timing_ff_asap7_max.rpt
report_checks -from _594_ -to _613_ -path_delay max -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/gcd_dir/timing_ff_asap7_max.rpt
report_checks -from _594_ -to _616_ -path_delay max -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/gcd_dir/timing_ff_asap7_max.rpt
report_checks -from _594_ -to _615_ -path_delay max -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/gcd_dir/timing_ff_asap7_max.rpt
report_checks -from _602_ -to _589_ -path_delay max -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/gcd_dir/timing_ff_asap7_max.rpt
report_checks -from _602_ -to _591_ -path_delay max -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/gcd_dir/timing_ff_asap7_max.rpt
report_checks -from _602_ -to _593_ -path_delay max -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/gcd_dir/timing_ff_asap7_max.rpt
report_checks -from _602_ -to _595_ -path_delay max -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/gcd_dir/timing_ff_asap7_max.rpt
report_checks -from _602_ -to _587_ -path_delay max -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/gcd_dir/timing_ff_asap7_max.rpt
report_checks -from _602_ -to _588_ -path_delay max -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/gcd_dir/timing_ff_asap7_max.rpt
report_checks -from _602_ -to _590_ -path_delay max -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/gcd_dir/timing_ff_asap7_max.rpt
report_checks -from _602_ -to _592_ -path_delay max -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/gcd_dir/timing_ff_asap7_max.rpt
report_checks -from _602_ -to _594_ -path_delay max -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/gcd_dir/timing_ff_asap7_max.rpt
report_checks -from _602_ -to _596_ -path_delay max -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/gcd_dir/timing_ff_asap7_max.rpt
report_checks -from _590_ -to _612_ -path_delay max -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/gcd_dir/timing_ff_asap7_max.rpt
report_checks -from _590_ -to _611_ -path_delay max -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/gcd_dir/timing_ff_asap7_max.rpt
report_checks -from _602_ -to _610_ -path_delay max -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/gcd_dir/timing_ff_asap7_max.rpt
report_checks -from _602_ -to _586_ -path_delay max -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/gcd_dir/timing_ff_asap7_max.rpt
report_checks -from _602_ -to _585_ -path_delay max -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/gcd_dir/timing_ff_asap7_max.rpt
report_checks -from _602_ -to _608_ -path_delay max -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/gcd_dir/timing_ff_asap7_max.rpt
report_checks -from _602_ -to _609_ -path_delay max -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/gcd_dir/timing_ff_asap7_max.rpt
report_checks -from _602_ -to _603_ -path_delay max -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/gcd_dir/timing_ff_asap7_max.rpt
report_checks -from _602_ -to _605_ -path_delay max -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/gcd_dir/timing_ff_asap7_max.rpt
report_checks -from _602_ -to _606_ -path_delay max -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/gcd_dir/timing_ff_asap7_max.rpt
report_checks -from _602_ -to _607_ -path_delay max -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/gcd_dir/timing_ff_asap7_max.rpt
report_checks -from _602_ -to _604_ -path_delay max -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/gcd_dir/timing_ff_asap7_max.rpt
report_checks -from _602_ -to _597_ -path_delay max -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/gcd_dir/timing_ff_asap7_max.rpt
report_checks -from _602_ -to _598_ -path_delay max -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/gcd_dir/timing_ff_asap7_max.rpt
report_checks -from _602_ -to _599_ -path_delay max -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/gcd_dir/timing_ff_asap7_max.rpt
report_checks -from _602_ -to _600_ -path_delay max -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/gcd_dir/timing_ff_asap7_max.rpt
report_checks -from _602_ -to _601_ -path_delay max -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/gcd_dir/timing_ff_asap7_max.rpt
report_checks -from _602_ -to _602_ -path_delay max -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/gcd_dir/timing_ff_asap7_max.rpt
report_checks -from _586_ -to _584_ -path_delay max -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/gcd_dir/timing_ff_asap7_max.rpt
report_checks -from _585_ -to _585_ -path_delay max -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/gcd_dir/timing_ff_asap7_max.rpt
report_checks -from _618_ -to _602_ -path_delay max -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/gcd_dir/timing_ff_asap7_max.rpt
report_checks -from _614_ -to _598_ -path_delay max -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/gcd_dir/timing_ff_asap7_max.rpt
report_checks -from _616_ -to _600_ -path_delay max -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/gcd_dir/timing_ff_asap7_max.rpt
report_checks -from _585_ -to _584_ -path_delay max -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/gcd_dir/timing_ff_asap7_max.rpt
report_checks -from _603_ -to _603_ -path_delay max -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/gcd_dir/timing_ff_asap7_max.rpt
report_checks -from _606_ -to _590_ -path_delay max -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/gcd_dir/timing_ff_asap7_max.rpt
report_checks -from _608_ -to _592_ -path_delay max -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/gcd_dir/timing_ff_asap7_max.rpt
report_checks -from _610_ -to _594_ -path_delay max -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/gcd_dir/timing_ff_asap7_max.rpt
report_checks -from _612_ -to _596_ -path_delay max -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/gcd_dir/timing_ff_asap7_max.rpt
report_checks -from _604_ -to _588_ -path_delay max -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/gcd_dir/timing_ff_asap7_max.rpt
report_checks -from _617_ -to _601_ -path_delay max -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/gcd_dir/timing_ff_asap7_max.rpt
report_checks -from _613_ -to _597_ -path_delay max -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/gcd_dir/timing_ff_asap7_max.rpt
report_checks -from _603_ -to _587_ -path_delay max -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/gcd_dir/timing_ff_asap7_max.rpt
report_checks -from _615_ -to _599_ -path_delay max -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/gcd_dir/timing_ff_asap7_max.rpt
report_checks -from _590_ -to _606_ -path_delay max -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/gcd_dir/timing_ff_asap7_max.rpt
report_checks -from _602_ -to _618_ -path_delay max -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/gcd_dir/timing_ff_asap7_max.rpt
report_checks -from _598_ -to _614_ -path_delay max -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/gcd_dir/timing_ff_asap7_max.rpt
report_checks -from _604_ -to _604_ -path_delay max -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/gcd_dir/timing_ff_asap7_max.rpt
report_checks -from _600_ -to _616_ -path_delay max -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/gcd_dir/timing_ff_asap7_max.rpt
report_checks -from _605_ -to _589_ -path_delay max -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/gcd_dir/timing_ff_asap7_max.rpt
report_checks -from _607_ -to _591_ -path_delay max -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/gcd_dir/timing_ff_asap7_max.rpt
report_checks -from _609_ -to _593_ -path_delay max -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/gcd_dir/timing_ff_asap7_max.rpt
report_checks -from _611_ -to _595_ -path_delay max -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/gcd_dir/timing_ff_asap7_max.rpt
report_checks -from _592_ -to _608_ -path_delay max -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/gcd_dir/timing_ff_asap7_max.rpt
report_checks -from _596_ -to _612_ -path_delay max -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/gcd_dir/timing_ff_asap7_max.rpt
report_checks -from _594_ -to _610_ -path_delay max -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/gcd_dir/timing_ff_asap7_max.rpt
report_checks -from _599_ -to _615_ -path_delay max -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/gcd_dir/timing_ff_asap7_max.rpt
report_checks -from _589_ -to _605_ -path_delay max -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/gcd_dir/timing_ff_asap7_max.rpt
report_checks -from _601_ -to _617_ -path_delay max -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/gcd_dir/timing_ff_asap7_max.rpt
report_checks -from _593_ -to _609_ -path_delay max -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/gcd_dir/timing_ff_asap7_max.rpt
report_checks -from _597_ -to _613_ -path_delay max -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/gcd_dir/timing_ff_asap7_max.rpt
report_checks -from _591_ -to _607_ -path_delay max -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/gcd_dir/timing_ff_asap7_max.rpt
report_checks -from _595_ -to _611_ -path_delay max -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/gcd_dir/timing_ff_asap7_max.rpt
report_checks -from _584_ -to _586_ -path_delay max -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/gcd_dir/timing_ff_asap7_max.rpt

# 生成hold time(min delay)报告
# set_operating_conditions min
report_checks -from _594_ -to _618_ -path_delay min -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/gcd_dir/timing_ff_asap7_min.rpt
report_checks -from _594_ -to _617_ -path_delay min -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/gcd_dir/timing_ff_asap7_min.rpt
report_checks -from _594_ -to _614_ -path_delay min -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/gcd_dir/timing_ff_asap7_min.rpt
report_checks -from _594_ -to _613_ -path_delay min -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/gcd_dir/timing_ff_asap7_min.rpt
report_checks -from _594_ -to _616_ -path_delay min -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/gcd_dir/timing_ff_asap7_min.rpt
report_checks -from _594_ -to _615_ -path_delay min -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/gcd_dir/timing_ff_asap7_min.rpt
report_checks -from _602_ -to _589_ -path_delay min -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/gcd_dir/timing_ff_asap7_min.rpt
report_checks -from _602_ -to _591_ -path_delay min -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/gcd_dir/timing_ff_asap7_min.rpt
report_checks -from _602_ -to _593_ -path_delay min -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/gcd_dir/timing_ff_asap7_min.rpt
report_checks -from _602_ -to _595_ -path_delay min -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/gcd_dir/timing_ff_asap7_min.rpt
report_checks -from _602_ -to _587_ -path_delay min -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/gcd_dir/timing_ff_asap7_min.rpt
report_checks -from _602_ -to _588_ -path_delay min -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/gcd_dir/timing_ff_asap7_min.rpt
report_checks -from _602_ -to _590_ -path_delay min -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/gcd_dir/timing_ff_asap7_min.rpt
report_checks -from _602_ -to _592_ -path_delay min -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/gcd_dir/timing_ff_asap7_min.rpt
report_checks -from _602_ -to _594_ -path_delay min -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/gcd_dir/timing_ff_asap7_min.rpt
report_checks -from _602_ -to _596_ -path_delay min -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/gcd_dir/timing_ff_asap7_min.rpt
report_checks -from _590_ -to _612_ -path_delay min -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/gcd_dir/timing_ff_asap7_min.rpt
report_checks -from _590_ -to _611_ -path_delay min -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/gcd_dir/timing_ff_asap7_min.rpt
report_checks -from _602_ -to _610_ -path_delay min -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/gcd_dir/timing_ff_asap7_min.rpt
report_checks -from _602_ -to _586_ -path_delay min -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/gcd_dir/timing_ff_asap7_min.rpt
report_checks -from _602_ -to _585_ -path_delay min -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/gcd_dir/timing_ff_asap7_min.rpt
report_checks -from _602_ -to _608_ -path_delay min -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/gcd_dir/timing_ff_asap7_min.rpt
report_checks -from _602_ -to _609_ -path_delay min -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/gcd_dir/timing_ff_asap7_min.rpt
report_checks -from _602_ -to _603_ -path_delay min -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/gcd_dir/timing_ff_asap7_min.rpt
report_checks -from _602_ -to _605_ -path_delay min -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/gcd_dir/timing_ff_asap7_min.rpt
report_checks -from _602_ -to _606_ -path_delay min -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/gcd_dir/timing_ff_asap7_min.rpt
report_checks -from _602_ -to _607_ -path_delay min -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/gcd_dir/timing_ff_asap7_min.rpt
report_checks -from _602_ -to _604_ -path_delay min -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/gcd_dir/timing_ff_asap7_min.rpt
report_checks -from _602_ -to _597_ -path_delay min -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/gcd_dir/timing_ff_asap7_min.rpt
report_checks -from _602_ -to _598_ -path_delay min -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/gcd_dir/timing_ff_asap7_min.rpt
report_checks -from _602_ -to _599_ -path_delay min -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/gcd_dir/timing_ff_asap7_min.rpt
report_checks -from _602_ -to _600_ -path_delay min -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/gcd_dir/timing_ff_asap7_min.rpt
report_checks -from _602_ -to _601_ -path_delay min -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/gcd_dir/timing_ff_asap7_min.rpt
report_checks -from _602_ -to _602_ -path_delay min -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/gcd_dir/timing_ff_asap7_min.rpt
report_checks -from _586_ -to _584_ -path_delay min -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/gcd_dir/timing_ff_asap7_min.rpt
report_checks -from _585_ -to _585_ -path_delay min -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/gcd_dir/timing_ff_asap7_min.rpt
report_checks -from _618_ -to _602_ -path_delay min -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/gcd_dir/timing_ff_asap7_min.rpt
report_checks -from _614_ -to _598_ -path_delay min -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/gcd_dir/timing_ff_asap7_min.rpt
report_checks -from _616_ -to _600_ -path_delay min -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/gcd_dir/timing_ff_asap7_min.rpt
report_checks -from _585_ -to _584_ -path_delay min -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/gcd_dir/timing_ff_asap7_min.rpt
report_checks -from _603_ -to _603_ -path_delay min -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/gcd_dir/timing_ff_asap7_min.rpt
report_checks -from _606_ -to _590_ -path_delay min -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/gcd_dir/timing_ff_asap7_min.rpt
report_checks -from _608_ -to _592_ -path_delay min -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/gcd_dir/timing_ff_asap7_min.rpt
report_checks -from _610_ -to _594_ -path_delay min -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/gcd_dir/timing_ff_asap7_min.rpt
report_checks -from _612_ -to _596_ -path_delay min -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/gcd_dir/timing_ff_asap7_min.rpt
report_checks -from _604_ -to _588_ -path_delay min -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/gcd_dir/timing_ff_asap7_min.rpt
report_checks -from _617_ -to _601_ -path_delay min -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/gcd_dir/timing_ff_asap7_min.rpt
report_checks -from _613_ -to _597_ -path_delay min -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/gcd_dir/timing_ff_asap7_min.rpt
report_checks -from _603_ -to _587_ -path_delay min -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/gcd_dir/timing_ff_asap7_min.rpt
report_checks -from _615_ -to _599_ -path_delay min -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/gcd_dir/timing_ff_asap7_min.rpt
report_checks -from _590_ -to _606_ -path_delay min -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/gcd_dir/timing_ff_asap7_min.rpt
report_checks -from _602_ -to _618_ -path_delay min -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/gcd_dir/timing_ff_asap7_min.rpt
report_checks -from _598_ -to _614_ -path_delay min -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/gcd_dir/timing_ff_asap7_min.rpt
report_checks -from _604_ -to _604_ -path_delay min -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/gcd_dir/timing_ff_asap7_min.rpt
report_checks -from _600_ -to _616_ -path_delay min -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/gcd_dir/timing_ff_asap7_min.rpt
report_checks -from _605_ -to _589_ -path_delay min -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/gcd_dir/timing_ff_asap7_min.rpt
report_checks -from _607_ -to _591_ -path_delay min -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/gcd_dir/timing_ff_asap7_min.rpt
report_checks -from _609_ -to _593_ -path_delay min -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/gcd_dir/timing_ff_asap7_min.rpt
report_checks -from _611_ -to _595_ -path_delay min -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/gcd_dir/timing_ff_asap7_min.rpt
report_checks -from _592_ -to _608_ -path_delay min -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/gcd_dir/timing_ff_asap7_min.rpt
report_checks -from _596_ -to _612_ -path_delay min -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/gcd_dir/timing_ff_asap7_min.rpt
report_checks -from _594_ -to _610_ -path_delay min -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/gcd_dir/timing_ff_asap7_min.rpt
report_checks -from _599_ -to _615_ -path_delay min -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/gcd_dir/timing_ff_asap7_min.rpt
report_checks -from _589_ -to _605_ -path_delay min -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/gcd_dir/timing_ff_asap7_min.rpt
report_checks -from _601_ -to _617_ -path_delay min -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/gcd_dir/timing_ff_asap7_min.rpt
report_checks -from _593_ -to _609_ -path_delay min -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/gcd_dir/timing_ff_asap7_min.rpt
report_checks -from _597_ -to _613_ -path_delay min -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/gcd_dir/timing_ff_asap7_min.rpt
report_checks -from _591_ -to _607_ -path_delay min -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/gcd_dir/timing_ff_asap7_min.rpt
report_checks -from _595_ -to _611_ -path_delay min -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/gcd_dir/timing_ff_asap7_min.rpt
report_checks -from _584_ -to _586_ -path_delay min -format full_clock_expanded >> /home/wllpro/llwang07/kxzhu/DelayPadding/gcd_dir/timing_ff_asap7_min.rpt
