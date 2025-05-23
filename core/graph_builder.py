import os
import subprocess
from typing import Dict, List, Tuple, Optional
import networkx as nx
import re
import sys

class TimingGraphBuilder:
    def __init__(self, netlist_path: str, corners_config: Dict[str, List[str]], work_dir: str = None):
        """
        初始化TimingGraphBuilder
        """
        self.netlist_path = netlist_path
        self.corners_config = corners_config
        self.graphs = {}  # 存储每个corner的timing graph
        self.work_dir = work_dir
        if not os.path.exists(self.work_dir):
            os.makedirs(self.work_dir)
    
    def _create_test_path_script(self, liberty_path: List[str]) -> str:
        """
        为指定工艺角创建OpenSTA脚本,来生成包括所有路径的setup和hold脚本
        """
        # 从网表文件中读取module名称
        module_name = None
        with open(self.netlist_path, 'r') as f:
            for line in f:
                if line.strip().startswith('module '):
                    module_name = line.strip().split()[1]
                    break
        if not module_name:
            print(f"Error: Could not find module name in {self.netlist_path}")
            return None
        script = "# 读取库文件和网表\n"
        for lib in liberty_path:
            script += f"read_liberty {lib}\n"
        script += f"read_verilog {self.netlist_path}\n"

        script += f"""
# 链接设计
link_design {module_name}

# 获取所有时钟
set clock_ports [get_ports "*clk*"]

# 创建时钟和约束
if {{$clock_ports != ""}} {{
    create_clock -name clk -period 10 $clock_ports
}}

# 生成setup time(max delay)报告
# set_operating_conditions max
report_checks -path_delay max -group_count 10000   -path_group clk -sort_by_slack > {self.work_dir}/path_max.rpt

# 生成hold time(min delay)报告
# set_operating_conditions min
report_checks -path_delay min -group_count 10000  -path_group clk -sort_by_slack > {self.work_dir}/path_min.rpt
"""
        script_path = f"{self.work_dir}/path_generate.tcl"
        with open(script_path, "w") as f:
            f.write(script)
            
        # 运行OpenSTA脚本
        result = subprocess.run(['/home/wllpro/llwang07/kxzhu/ssta/OpenSTA_D/app/sta', '-exit', script_path], 
                              capture_output=True, text=True, cwd=self.work_dir)
        
        if result.returncode != 0:
            print(f"Error running OpenSTA.")
            print(result.stderr)
            return None, None
        
        # 从path_min.rpt和path_max.rpt中提取所有起点和终点
        path = []
        
        # 读取path_max.rpt
        if os.path.exists(f"{self.work_dir}/path_max.rpt"):
            with open(f"{self.work_dir}/path_max.rpt", "r") as f:
                content = f.read()
                # 匹配 Startpoint 和 Endpoint 的名称（包括可能的层级）
                startpoint_matches = re.findall(r"Startpoint:\s+([^\s(]+)", content)
                endpoint_matches = re.findall(r"Endpoint:\s+([^\s(]+)", content)
                # 将startpoint和endpoint组合成tuple
                path_pairs = list(zip(startpoint_matches, endpoint_matches))
                path.extend(path_pairs)
                
        # 读取path_min.rpt
        if os.path.exists(f"{self.work_dir}/path_min.rpt"):
            with open(f"{self.work_dir}/path_min.rpt", "r") as f:
                content = f.read()
                # 匹配 Startpoint 和 Endpoint 的名称（包括可能的层级）
                startpoint_matches = re.findall(r"Startpoint:\s+([^\s(]+)", content)
                endpoint_matches = re.findall(r"Endpoint:\s+([^\s(]+)", content)
                # 将startpoint和endpoint组合成tuple
                path_pairs = list(zip(startpoint_matches, endpoint_matches))
                path.extend(path_pairs)
        
        # print(f"path: {path}")
        return path

    
    def _create_sta_script(self, corner: str, liberty_path: List[str], path: List[Tuple[str, str]]) -> str:
        """
        为指定工艺角创建OpenSTA脚本,生成setup和hold时序报告
        
        Args:
            corner: 工艺角名称
            liberty_path: Liberty文件路径
            path: 路径列表
        Returns:
            str: 生成的TCL脚本内容
        """
        # 从网表文件中读取module名称
        module_name = None
        with open(self.netlist_path, 'r') as f:
            for line in f:
                if line.strip().startswith('module '):
                    module_name = line.strip().split()[1]
                    break
        
        if not module_name:
            print(f"Error: Could not find module name in {self.netlist_path}")
            return None
        script = "# 读取库文件和网表\n"
        for lib in liberty_path:
            script += f"read_liberty {lib}\n"
        script += f"read_verilog {self.netlist_path}\n"

        script += f"""
# 链接设计
link_design {module_name}

# 获取所有时钟
set clock_ports [get_ports "*clk*"]

# 创建时钟和约束
if {{$clock_ports != ""}} {{
    create_clock -name clk -period 10 $clock_ports
}}

# 生成setup time(max delay)报告
# set_operating_conditions max
"""
        # 为每个路径生成max delay报告
        for start, end in path:
            script += f"report_checks -from {start} -to {end} -path_delay max -format full_clock_expanded >> {self.work_dir}/timing_{corner}_max.rpt\n"

        script += f"""
# 生成hold time(min delay)报告
# set_operating_conditions min
"""
        # 为每个路径生成min delay报告
        for start, end in path:
            script += f"report_checks -from {start} -to {end} -path_delay min -format full_clock_expanded >> {self.work_dir}/timing_{corner}_min.rpt\n"

        return script
        
    def _parse_timing_report(self, corner: str) -> Optional[nx.DiGraph]:
        """
        解析OpenSTA的timing报告并构建图。图的节点为寄存器,边表示setup和hold delay
        
        Args:
            corner: 工艺角名称
            
        Returns:
            nx.DiGraph: 构建的有向图,如果失败则返回None
        """
        max_timing_file = f"{self.work_dir}/timing_{corner}_max.rpt"
        min_timing_file = f"{self.work_dir}/timing_{corner}_min.rpt"
        
        if not (os.path.exists(max_timing_file) and os.path.exists(min_timing_file)):
            return None
            
        graph = nx.DiGraph()
        print(f"开始解析timing report: {max_timing_file} 和 {min_timing_file}")
        
        # 处理setup time(max delay)路径
        def process_setup_timing_path(file_path: str, delay_type: str):
            with open(file_path, 'r') as f:
                timing_content = f.read()
                #print(timing_content)
                # 匹配所有timing路径
            path_sections = re.finditer(
                r'Startpoint:\s+(\S+)\s+\((.*?)\).*?'               # group(1,2): Startpoint
                r'Endpoint:\s+(\S+)\s+\((.*?)\).*?'                 # group(3,4): Endpoint
                r'Path Group:.*?\n'
                r'Path Type:.*?\n'
                r'(.*?)^\s*[-\d\.]+\s+slack.*?$'                    # group(5): Path body until 'slack'
                ,
                timing_content,
                re.DOTALL | re.MULTILINE
            )

                
            for match in path_sections:
                start_reg = match.group(1)
                start_type = match.group(2)
                end_reg = match.group(3)
                end_type = match.group(4)
                path_detail = match.group(5)
                # print(f"path_detail: {path_detail}")
                # 提取 arrival/required/setup
                arrival_time = None
                setup_time = None
                arrival_match = re.search(r'\n\s*([\d\.\-]+)\s+data arrival time', path_detail)
                setup_match = re.search(r'\n\s*([\d\.\-]+)\s+[\d\.\-]+\s+library setup time', path_detail)
                if arrival_match:
                    arrival_time = float(arrival_match.group(1))
                if setup_match:
                    setup_time = float(setup_match.group(1))

                print(f"start_reg: {start_reg}, end_reg: {end_reg}, arrival: {arrival_time}, setup: {setup_time}")

                # 添加节点和边
                if start_reg not in graph:
                    graph.add_node(start_reg, type='register')
                if end_reg not in graph:
                    graph.add_node(end_reg, type='register')

                if graph.has_edge(start_reg, end_reg):
                    graph[start_reg][end_reg][delay_type] = {
                        "arrival_time": arrival_time,
                        "library_time": setup_time,
                    }
                else:
                    graph.add_edge(start_reg, end_reg, **{
                        delay_type: {
                            "arrival_time": arrival_time,
                            "library_time": setup_time,
                        }
                    })
                    if not nx.is_directed_acyclic_graph(graph):
                        graph.remove_edge(start_reg, end_reg)
                        print(f"⚠️  Skipped edge {start_reg} → {end_reg} to avoid cycle.")

        # 处理hold time(min delay)路径
        def process_hold_timing_path(file_path: str, delay_type: str):
            with open(file_path, 'r') as f:
                timing_content = f.read()
                #print(timing_content)
                # 匹配所有timing路径
            path_sections = re.finditer(
                r'Startpoint:\s+(\S+)\s+\((.*?)\).*?'               # group(1,2): Startpoint
                r'Endpoint:\s+(\S+)\s+\((.*?)\).*?'                 # group(3,4): Endpoint
                r'Path Group:.*?\n'
                r'Path Type:.*?\n'
                r'(.*?)^\s*[-\d\.]+\s+slack.*?$'                    # group(5): Path body until 'slack'
                ,
                timing_content,
                re.DOTALL | re.MULTILINE
            )

                
            for match in path_sections:
                start_reg = match.group(1)
                start_type = match.group(2)
                end_reg = match.group(3)
                end_type = match.group(4)
                path_detail = match.group(5)
                # print(f"path_detail: {path_detail}")
                # 提取 arrival/required/setup
                arrival_time = None
                hold_time = None
                arrival_match = re.search(r'\n\s*([\d\.\-]+)\s+data arrival time', path_detail)
                hold_match = re.search(r'\n\s*([\d\.\-]+)\s+[\d\.\-]+\s+library hold time', path_detail)
                if arrival_match:
                    arrival_time = float(arrival_match.group(1))
                if hold_match:
                    hold_time = float(hold_match.group(1))

                print(f"start_reg: {start_reg}, end_reg: {end_reg}, arrival: {arrival_time}, hold: {hold_time}")

                # 添加节点和边
                if start_reg not in graph:
                    graph.add_node(start_reg, type='register')
                if end_reg not in graph:
                    graph.add_node(end_reg, type='register')

                if graph.has_edge(start_reg, end_reg):
                    graph[start_reg][end_reg][delay_type] = {
                        "arrival_time": arrival_time,
                        "library_time": hold_time,
                    }
                else:
                    graph.add_edge(start_reg, end_reg, **{
                        delay_type: {
                            "arrival_time": arrival_time,
                            "library_time": hold_time,
                        }
                    })
                    if not nx.is_directed_acyclic_graph(graph):
                        graph.remove_edge(start_reg, end_reg)
                        #print(f"⚠️  Skipped edge {start_reg} → {end_reg} to avoid cycle.")


        # 处理max delay(setup)和min delay(hold)报告
        process_setup_timing_path(max_timing_file, 'setup_delay')
        process_hold_timing_path(min_timing_file, 'hold_delay')
        
        return graph
            
    def _run_sta_analysis(self, corner: str, liberty_path: List[str], path: List[Tuple[str, str]]) -> Optional[nx.DiGraph]:
        """
        运行OpenSTA时序分析并构建图
        
        Args:
            corner: 工艺角名称
            liberty_path: Liberty文件路径
            
        Returns:
            nx.DiGraph: 构建的有向图，如果失败则返回None
        """
        # 创建临时TCL脚本
        script_path = f"{self.work_dir}/temp_{corner}.tcl"
        with open(script_path, 'w') as f:
            f.write(self._create_sta_script(corner, liberty_path, path))
        
        
        
        print("运行OpenSTA")
        try:
            # 运行OpenSTA
            result = subprocess.run(['/home/wllpro/llwang07/kxzhu/ssta/OpenSTA_D/app/sta', '-exit', script_path], 
                                 capture_output=True, 
                                 text=True,
                                 cwd=self.work_dir)
            
            
            if not os.path.exists(f"{self.work_dir}/timing_{corner}_max.rpt") or not os.path.exists(f"{self.work_dir}/timing_{corner}_min.rpt"):
                print(f"未找到timing_{corner}_max.rpt或timing_{corner}_min.rpt文件")
                return None
                
            # 解析输出并构建图
            return self._parse_timing_report(corner)
            
        except Exception as e:
            print(f"Error running STA for corner {corner}: {str(e)}")
            return None
        # finally:
        #     # 清理临时文件
        #     for file in [script_path, f"timing_{corner}.rpt", f"nets_{corner}.rpt"]:
        #         if os.path.exists(file):
        #             os.remove(file)
                
    def build_timing_graphs(self) -> Dict[str, nx.DiGraph]:
        """
        构建所有工艺角的timing graphs
        
        Returns:
            Dict[str, nx.DiGraph]: 键为工艺角名称，值为对应的timing graph
        """
        liberty_path = next(iter(self.corners_config.values()))
        path = self._create_test_path_script(liberty_path)
        print(f"config: {self.corners_config}")
        for corner, liberty_path in self.corners_config.items():
            graph = self._run_sta_analysis(corner, liberty_path, path)
            if graph is not None:
                self.graphs[corner] = graph
                
        return self.graphs
        
    def get_critical_paths(self, corner: str, num_paths: int = 1) -> List[List[str]]:
        """
        获取指定工艺角的关键路径
        
        Args:
            corner: 工艺角名称
            num_paths: 需要返回的关键路径数量
            
        Returns:
            List[List[str]]: 关键路径列表
        """
        if corner not in self.graphs:
            return []
            
        graph = self.graphs[corner]
        paths = []
        
        # 找到所有输入和输出端口
        input_ports = [n for n, d in graph.nodes(data=True) 
                      if d.get('type') == 'input']
        output_ports = [n for n, d in graph.nodes(data=True) 
                       if d.get('type') == 'output']
        
        # 对每个输入输出端口对寻找关键路径
        for source in input_ports:
            for target in output_ports:
                try:
                    path = nx.shortest_path(graph, source, target, 
                                         weight='weight', method='bellman-ford')
                    delay = self.get_path_delay(corner, path)
                    paths.append((delay, path))
                except nx.NetworkXNoPath:
                    continue
                    
        # 按延迟排序并返回前num_paths条路径
        paths.sort(reverse=True)  # 按延迟降序排序
        return [path for _, path in paths[:num_paths]]
        
    def get_path_delay(self, corner: str, path: List[str]) -> float:
        """
        计算指定路径在给定工艺角下的延迟
        
        Args:
            corner: 工艺角名称
            path: 路径节点列表
            
        Returns:
            float: 路径总延迟
        """
        if corner not in self.graphs:
            return 0.0
            
        graph = self.graphs[corner]
        total_delay = 0.0
        
        for i in range(len(path) - 1):
            current_node = path[i]
            next_node = path[i + 1]
            if graph.has_edge(current_node, next_node):
                total_delay += graph[current_node][next_node]['weight']
                
        return total_delay

    def print_graph_info(self, corner: str) -> None:
        """
        打印指定工艺角的图信息
        
        Args:
            corner: 工艺角名称
        """
        if corner not in self.graphs:
            print(f"错误：未找到工艺角 {corner} 的图")
            return
            
        graph = self.graphs[corner]
        
        print(f"\n{'='*50}")
        print(f"工艺角 {corner} 的图信息:")
        print(f"{'='*50}")
        
        # 基本信息
        print(f"\n1. 基本统计信息:")
        print(f"   - 寄存器总数: {len(graph.nodes())}")
        print(f"   - 时序路径总数: {len(graph.edges())}")
        
        # # 节点信息
        # print(f"\n2. 寄存器节点信息:")
        # print(f"   {'寄存器名称':<50}")
        # print(f"   {'-'*50}")
        # for node in graph.nodes():
        #     print(f"   {node:<50}")
            
        # 边信息(时序路径)
        #print(f"\n3. 时序路径信息:")
        #print(f"   {'起点寄存器':<40} {'终点寄存器':<40} {'Setup Delay(ns)':<15} {'Hold Delay(ns)':<15}")
        #print(f"   {'-'*110}")
        for u, v, data in graph.edges(data=True):
            setup_info = data.get('setup_delay', {})
            hold_info = data.get('hold_delay', {})

            setup_arrival = setup_info.get("arrival_time", "N/A")
            hold_arrival = hold_info.get("arrival_time", "N/A")
            setup_library = setup_info.get("library_time", "N/A")
            hold_library = hold_info.get("library_time", "N/A")
            if isinstance(setup_arrival, (int, float)):
                setup_arrival = f"{setup_arrival:.3f}"
            if isinstance(hold_arrival, (int, float)):
                hold_arrival = f"{hold_arrival:.3f}"
            if isinstance(setup_library, (int, float)):
                setup_library = f"{setup_library:.3f}"
            if isinstance(hold_library, (int, float)):
                hold_library = f"{hold_library:.3f}"
            print(f"   {u:<40} {v:<40} {setup_arrival:<15} {hold_arrival:<15} {setup_library:<15} {hold_library:<15}")
            
        # 关键路径信息
        # print(f"\n4. 关键路径分析:")
        
        #  Setup时间关键路径
        # max_setup_delay = 0.0
        # setup_critical_path = None
        # for u, v, data in graph.edges(data=True):
        #     setup_delay = data.get('setup_delay', 0.0)
        #     if isinstance(setup_delay, (int, float)) and setup_delay > max_setup_delay:
        #         max_setup_delay = setup_delay
        #         setup_critical_path = (u, v)
        
        # if setup_critical_path:
        #     print(f"\n   Setup时间关键路径:")
        #     print(f"   - 起点寄存器: {setup_critical_path[0]}")
        #     print(f"   - 终点寄存器: {setup_critical_path[1]}")
        #     print(f"   - Setup Delay: {max_setup_delay:.3f}ns")
            
        # # Hold时间关键路径
        # max_hold_delay = 0.0
        # hold_critical_path = None
        # for u, v, data in graph.edges(data=True):
        #     hold_delay = data.get('hold_delay', 0.0)
        #     if isinstance(hold_delay, (int, float)) and hold_delay > max_hold_delay:
        #         max_hold_delay = hold_delay
        #         hold_critical_path = (u, v)
                
        # if hold_critical_path:
        #     print(f"\n   Hold时间关键路径:")
        #     print(f"   - 起点寄存器: {hold_critical_path[0]}")
        #     print(f"   - 终点寄存器: {hold_critical_path[1]}")
        #     print(f"   - Hold Delay: {max_hold_delay:.3f}ns")
            
        # print(f"\n{'='*50}\n")
            
            
def create_timing_graphs(netlist_path: str, corners_config: Dict[str, List[str]], work_dir: str = None) -> TimingGraphBuilder:
    """
    创建TimingGraphBuilder实例并构建timing graphs的便捷函数
    
    Args:
        netlist_path: Verilog网表文件路径
        corners_config: 工艺角配置字典，格式为 {"corner_name": ["liberty_file_path1", "liberty_file_path2"]}
        
    Returns:
        TimingGraphBuilder: 构建好的TimingGraphBuilder实例
    """
    builder = TimingGraphBuilder(netlist_path, corners_config, work_dir=work_dir)
    builder.build_timing_graphs()
    return builder

def _test_timing_analysis():
    """测试时序分析功能"""
    try:
        # 配置测试参数
        project_root = "/home/wllpro/llwang07/kxzhu/DelayPadding"
        
        # 设置网表和Liberty文件路径
        netlist_path = os.path.join(project_root, "netlist", "/home/wllpro/llwang07/kxzhu/ssta/distribution/vlsi/gcd/gcd.v")  
        corners_config = {
            'ss_asap7': [
                "/home/wllpro/llwang07/kxzhu/DelayPadding/platform/asap7sc7p5t_AO_RVT_SS_nldm_211120.lib",
                "/home/wllpro/llwang07/kxzhu/DelayPadding/platform/asap7sc7p5t_INVBUF_RVT_SS_nldm_220122.lib",
                "/home/wllpro/llwang07/kxzhu/DelayPadding/platform/asap7sc7p5t_OA_RVT_SS_nldm_211120.lib",
                "/home/wllpro/llwang07/kxzhu/DelayPadding/platform/asap7sc7p5t_SEQ_RVT_SS_nldm_220123.lib",
                "/home/wllpro/llwang07/kxzhu/DelayPadding/platform/asap7sc7p5t_SIMPLE_RVT_SS_nldm_211120.lib"
            ],
            'ff_asap7': [
                "/home/wllpro/llwang07/kxzhu/DelayPadding/platform/asap7sc7p5t_AO_RVT_FF_nldm_211120.lib",
                "/home/wllpro/llwang07/kxzhu/DelayPadding/platform/asap7sc7p5t_INVBUF_RVT_FF_nldm_220122.lib",
                "/home/wllpro/llwang07/kxzhu/DelayPadding/platform/asap7sc7p5t_OA_RVT_FF_nldm_211120.lib",
                "/home/wllpro/llwang07/kxzhu/DelayPadding/platform/asap7sc7p5t_SEQ_RVT_FF_nldm_220123.lib",
                "/home/wllpro/llwang07/kxzhu/DelayPadding/platform/asap7sc7p5t_SIMPLE_RVT_FF_nldm_211120.lib"
            ]
        }
        work_dir = "/home/wllpro/llwang07/kxzhu/DelayPadding/gcd_dir"
        # 检查必要文件是否存在
        required_files = [netlist_path] 
        for libs in corners_config.values():
            required_files.extend(libs)
        for file_path in required_files:
            if not os.path.exists(file_path):
                print(f"错误: 找不到必要的文件 {file_path}")
                print("请确保以下文件存在:")
                print(f"1. 网表文件: {netlist_path}")
                print(f"2. 慢角Liberty文件: {corners_config['ss_asap7']}")
                print(f"3. 快角Liberty文件: {corners_config['ff_asap7']}")
                return False
        
        # 创建TimingGraphBuilder实例
        print("\n初始化TimingGraphBuilder...")
        print(f"使用网表: {netlist_path}")
        for corner, libs in corners_config.items():
            print(f"工艺角 {corner}: {libs}")
        print(f"工作目录: {work_dir}")

        builder = create_timing_graphs(
            netlist_path=netlist_path,
            corners_config=corners_config,
            work_dir=work_dir
        )
        
        # 测试关键路径分析
        # print("\n分析关键路径...")
        # for corner in corners_config.keys():
        #     print(f"\n=== {corner} corner ===")
        #     paths = builder.get_critical_paths(corner, num_paths=2)
            
        #     if not paths:
        #         print(f"警告: 在{corner}角没有找到关键路径")
        #         continue
                
        #     for i, path in enumerate(paths, 1):
        #         delay = builder.get_path_delay(corner, path)
        #         print(f"\n关键路径 {i}:")
        #         print(f"延迟: {delay:.3f}ns")
        #         print("路径: " + " -> ".join(path))
        
        # 打印图信息
        #print("\n打印图信息...")
        # for corner in corners_config.keys():
        #     builder.print_graph_info(corner)
            
        #print("\n测试完成!")
        return True
        
    except Exception as e:
        print(f"测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # 运行测试
    success = _test_timing_analysis()
    sys.exit(0 if success else 1)