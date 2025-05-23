import os
import subprocess
from typing import Dict, List, Tuple, Optional
import networkx as nx
import re
import sys

class TimingGraphBuilder:
    def __init__(self, netlist_path: str, corners_config: Dict[str, str]):
        """
        初始化TimingGraphBuilder
        """
        self.netlist_path = netlist_path
        self.corners_config = corners_config
        self.graphs = {}  # 存储每个corner的timing graph
            
    def _create_sta_script(self, corner: str, liberty_path: str) -> str:
        """
        为指定工艺角创建OpenSTA脚本,生成setup和hold时序报告
        
        Args:
            corner: 工艺角名称
            liberty_path: Liberty文件路径
            
        Returns:
            str: 生成的TCL脚本内容
        """
        script = f"""
                    # 读取库文件和网表
                    read_liberty {liberty_path}
                    read_verilog {self.netlist_path}
                    
                    # 链接设计
                    link_design top
                    
                    # 获取所有时钟
                    set clock_ports [get_ports "*clk*"]
                    
                    # 创建时钟和约束
                    if {{$clock_ports != ""}} {{
                        create_clock -name clk -period 10 $clock_ports
                    }}
                    
                    # 生成setup time(max delay)报告
                    set_operating_conditions max
                    report_checks -path_delay max -unconstrained -format full_clock_expanded > timing_{corner}_max.rpt
                    
                    # 生成hold time(min delay)报告
                    set_operating_conditions min
                    report_checks -path_delay min -unconstrained -format full_clock_expanded > timing_{corner}_min.rpt
                    """
        return script
        
    def _parse_timing_report(self, corner: str) -> Optional[nx.DiGraph]:
        """
        解析OpenSTA的timing报告并构建图。图的节点为寄存器,边表示setup和hold delay
        
        Args:
            corner: 工艺角名称
            
        Returns:
            nx.DiGraph: 构建的有向图,如果失败则返回None
        """
        max_timing_file = f"timing_{corner}_max.rpt"
        min_timing_file = f"timing_{corner}_min.rpt"
        
        if not (os.path.exists(max_timing_file) and os.path.exists(min_timing_file)):
            return None
            
        graph = nx.DiGraph()
        
        # 处理setup time(max delay)路径
        def process_timing_path(file_path: str, delay_type: str):
            with open(file_path, 'r') as f:
                timing_content = f.read()
                
                # 匹配所有timing路径
                path_sections = re.finditer(
                    r'Startpoint:\s+(\S+)\s+\((.*?)\).*?'
                    r'Endpoint:\s+(\S+)\s+\((.*?)\).*?'
                    r'Delay\s+Time\s+Description\s*\n[-]+\n(.*?)(?:\n\s*[\d\.\-]*\s*data arrival time)',
                    timing_content,
                    re.DOTALL
                )
                
                for match in path_sections:
                    start_reg = match.group(1)
                    start_type = match.group(2)
                    end_reg = match.group(3)
                    end_type = match.group(4)
                    
                    # 只处理寄存器到寄存器的路径
                    if not ('register' in start_type.lower() and 'register' in end_type.lower()):
                        continue
                        
                    # 添加寄存器节点
                    if start_reg not in graph:
                        graph.add_node(start_reg, type='register')
                    if end_reg not in graph:
                        graph.add_node(end_reg, type='register')
                    
                    # 计算路径总延迟
                    path_lines = match.group(5).strip().split('\n')
                    total_delay = 0.0
                    for line in path_lines:
                        if line.strip():
                            try:
                                delay = float(line.strip().split()[0])
                                total_delay += delay
                            except (ValueError, IndexError):
                                continue
                    
                    # 添加或更新边的延迟信息
                    if graph.has_edge(start_reg, end_reg):
                        graph[start_reg][end_reg][delay_type] = total_delay
                    else:
                        graph.add_edge(start_reg, end_reg, **{delay_type: total_delay})
        
        # 处理max delay(setup)和min delay(hold)报告
        process_timing_path(max_timing_file, 'setup_delay')
        process_timing_path(min_timing_file, 'hold_delay')
        
        return graph
            
    def _run_sta_analysis(self, corner: str, liberty_path: str) -> Optional[nx.DiGraph]:
        """
        运行OpenSTA时序分析并构建图
        
        Args:
            corner: 工艺角名称
            liberty_path: Liberty文件路径
            
        Returns:
            nx.DiGraph: 构建的有向图，如果失败则返回None
        """
        # 创建临时TCL脚本
        script_path = f"temp_{corner}.tcl"
        with open(script_path, 'w') as f:
            f.write(self._create_sta_script(corner, liberty_path))
        
        print("运行OpenSTA")
        try:
            # 运行OpenSTA
            result = subprocess.run(['/home/wllpro/llwang07/kxzhu/ssta/OpenSTA_D/app/sta', ' -exit', script_path], 
                                 capture_output=True, 
                                 text=True)
            
            if not os.path.exists(f"timing_{corner}.rpt"):
                print(f"未找到timing_{corner}.rpt文件")
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
        for corner, liberty_path in self.corners_config.items():
            graph = self._run_sta_analysis(corner, liberty_path)
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
        print(f"   - 节点总数: {len(graph.nodes())}")
        print(f"   - 边总数: {len(graph.edges())}")
        
        # 节点信息
        print(f"\n2. 节点详细信息:")
        print(f"   {'节点名称':<40} {'实例名':<30} {'引脚名':<20} {'单元类型':<20}")
        print(f"   {'-'*110}")
        for node, data in graph.nodes(data=True):
            instance = data.get('instance', 'N/A')
            pin = data.get('pin', 'N/A')
            cell_type = data.get('cell_type', 'N/A')
            print(f"   {node:<40} {instance:<30} {pin:<20} {cell_type:<20}")
            
        # 边信息
        print(f"\n3. 边延迟信息:")
        print(f"   {'起点':<40} {'终点':<40} {'延迟(ns)':<10}")
        print(f"   {'-'*90}")
        for u, v, data in graph.edges(data=True):
            delay = data.get('weight', 0.0)
            print(f"   {u:<40} {v:<40} {delay:<10.3f}")
            
        # # 关键路径信息
        # print(f"\n4. 关键路径分析:")
        # try:
        #     # 找到所有起点（入度为0的节点）
        #     start_nodes = [n for n in graph.nodes() if graph.in_degree(n) == 0]
        #     # 找到所有终点（出度为0的节点）
        #     end_nodes = [n for n in graph.nodes() if graph.out_degree(n) == 0]
            
        #     max_delay = 0.0
        #     critical_path = None
            
        #     # 计算所有路径中的最长延迟路径
        #     for start in start_nodes:
        #         for end in end_nodes:
        #             try:
        #                 paths = list(nx.all_simple_paths(graph, start, end))
        #                 for path in paths:
        #                     delay = sum(graph[path[i]][path[i+1]]['weight'] 
        #                               for i in range(len(path)-1))
        #                     if delay > max_delay:
        #                         max_delay = delay
        #                         critical_path = path
        #             except nx.NetworkXNoPath:
        #                 continue
            
        #     if critical_path:
        #         print(f"   最大延迟: {max_delay:.3f}ns")
        #         print(f"   关键路径:")
        #         print(f"   {' -> '.join(critical_path)}")
        #     else:
        #         print("   未找到有效的时序路径")
                
        # except Exception as e:
        #     print(f"   计算关键路径时出错: {str(e)}")
            
        # print(f"\n{'='*50}\n")
        
            
def create_timing_graphs(netlist_path: str, corners_config: Dict[str, str]) -> TimingGraphBuilder:
    """
    创建TimingGraphBuilder实例并构建timing graphs的便捷函数
    
    Args:
        netlist_path: Verilog网表文件路径
        corners_config: 工艺角配置字典，格式为 {"corner_name": "liberty_file_path"}
        
    Returns:
        TimingGraphBuilder: 构建好的TimingGraphBuilder实例
    """
    builder = TimingGraphBuilder(netlist_path, corners_config)
    builder.build_timing_graphs()
    return builder

def _test_timing_analysis():
    """测试时序分析功能"""
    try:
        # 配置测试参数
        project_root = "/home/wllpro/llwang07/kxzhu/DelayPadding"
        
        # 设置网表和Liberty文件路径
        netlist_path = os.path.join(project_root, "netlist", "/home/wllpro/llwang07/kxzhu/ssta/OpenSTA_D/examples/example1.v")  # 你需要提供这个文件
        corners_config = {
            'ss_nangate45': os.path.join(project_root, "library", "/home/wllpro/llwang07/kxzhu/ssta/OpenSTA_D/examples/nangate45_slow.lib"),  # 你需要提供这个文件
            'ff_nangate45': os.path.join(project_root, "library", "/home/wllpro/llwang07/kxzhu/ssta/OpenSTA_D/examples/nangate45_fast.lib")      # 你需要提供这个文件
        }
        
        # 检查必要文件是否存在
        required_files = [netlist_path] + list(corners_config.values())
        for file_path in required_files:
            if not os.path.exists(file_path):
                print(f"错误: 找不到必要的文件 {file_path}")
                print("请确保以下文件存在:")
                print(f"1. 网表文件: {netlist_path}")
                print(f"2. 慢角Liberty文件: {corners_config['ss_nangate45']}")
                print(f"3. 快角Liberty文件: {corners_config['ff_nangate45']}")
                return False
        
        # 创建TimingGraphBuilder实例
        print("\n初始化TimingGraphBuilder...")
        print(f"使用网表: {netlist_path}")
        for corner, lib in corners_config.items():
            print(f"工艺角 {corner}: {lib}")
            
        builder = create_timing_graphs(
            netlist_path=netlist_path,
            corners_config=corners_config
        )
        
        # 测试关键路径分析
        print("\n分析关键路径...")
        for corner in corners_config.keys():
            print(f"\n=== {corner} corner ===")
            paths = builder.get_critical_paths(corner, num_paths=2)
            
            if not paths:
                print(f"警告: 在{corner}角没有找到关键路径")
                continue
                
            for i, path in enumerate(paths, 1):
                delay = builder.get_path_delay(corner, path)
                print(f"\n关键路径 {i}:")
                print(f"延迟: {delay:.3f}ns")
                print("路径: " + " -> ".join(path))
        
        # 打印图信息
        print("\n打印图信息...")
        for corner in corners_config.keys():
            builder.print_graph_info(corner)
            
        print("\n测试完成!")
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