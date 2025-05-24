import cvxpy as cp
import networkx as nx
from collections import defaultdict

def delay_padding_lp_solver(corner_graphs, T_clk, alpha=0.1, beta=0.1):
    """
    使用CVXPY求解Delay Padding的LP问题
    
    参数:
        corner_graphs (dict): 多Corner时序图,格式为 {corner: nx.Graph}.
        T_clk (float): 时钟周期.
        alpha (float): 电势平滑项系数.
        beta (float): Buffer插入成本系数.
    
    返回:
        dict: 优化后的全局电势 {node: potential}.
    """
    # --------------------- 数据准备 ---------------------
    # 提取所有节点并编号
    all_nodes = set()
    for G in corner_graphs.values():
        all_nodes.update(G.nodes())
    nodes = sorted(all_nodes)
    node_id = {node: idx for idx, node in enumerate(nodes)}
    num_nodes = len(nodes)

    # 定义CVXPY变量：电势 p
    p = cp.Variable(num_nodes, name="p")

    # --------------------- 构建目标函数 ---------------------
    # 目标函数 = 平滑项（电势变化平方和） + Buffer插入成本（电势差和）
    smooth_cost = alpha * cp.sum_squares(p)  # 示例：简化平滑项，实际需根据边定义
    buffer_cost = beta * cp.sum(cp.pos(p[1:] - p[:-1]))  # 假设Buffer与正电势差相关
    total_cost = smooth_cost + buffer_cost

    # --------------------- 构建约束 ---------------------
    constraints = []

    # 遍历每个Corner的时序约束
    for corner, G in corner_graphs.items():
        for u, v in G.edges():
            u_idx = node_id[u]
            v_idx = node_id[v]
            
            # 添加Setup约束：p[v] - p[u] <= T_clk - t_su_lib - arrival_time
            setup_data = G.get_edge_data(u, v).get("setup", {})
            if setup_data:
                t_su_lib = setup_data["library_time"]  # 库的Setup时间
                arrival = setup_data["arrival_time"]   # 数据路径固有延迟
                T_setup_margin = T_clk + t_su_lib
                setup_constraint = p[v_idx] - p[u_idx] <= T_setup_margin - arrival
                constraints.append(setup_constraint)
            
            # 添加Hold约束：p[v] - p[u] >= arrival_time - t_hold_lib
            hold_data = G.get_edge_data(u, v).get("hold", {})
            if hold_data:
                t_hold_lib = hold_data["library_time"]  # 库的Hold时间
                arrival = hold_data["arrival_time"]
                hold_constraint = p[v_idx] - p[u_idx] >= arrival - t_hold_lib
                constraints.append(hold_constraint)

    # --------------------- 求解LP问题 ---------------------
    problem = cp.Problem(cp.Minimize(total_cost), constraints)
    problem.solve(solver=cp.ECOS, verbose=False)  # 使用ECOS求解器（开源）

    # --------------------- 处理结果 ---------------------
    if problem.status == "optimal":
        p_optimal = {node: p.value[node_id[node]] for node in nodes}
        print(f"LP求解成功. 状态: {problem.status}")
        return p_optimal
    else:
        raise RuntimeError(f"不可行或无解. 状态: {problem.status}")
