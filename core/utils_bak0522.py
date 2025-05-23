import numpy as np
from typing import Dict
import networkx as nx

def build_arrival_dict_from_graph(G, delay_attr="setup_delay"):
    """
    将 DiGraph 中每个节点的最大/最小 arrival time 通过路径传播法构建。
    每条边表示 FF→FF 的端到端延时。
    """
    arrival = {}
    for u, v, data in G.edges(data=True):
        delay = float(data.get(delay_attr, 0.0))
        if u not in arrival:
            arrival[u] = 0.0
        candidate_v = arrival[u] + delay
        arrival[v] = max(arrival.get(v, float("-inf")), candidate_v)
    return arrival

def initialize_y_k(corner_graphs, mode="setup"):
    delay_attr = "setup_delay" if mode == "setup" else "hold_delay"
    y_k = {}
    for corner, G in corner_graphs.items():
        arrival = build_arrival_dict_from_graph(G, delay_attr)
        y_k[corner] = np.array([arrival.get(n, 0.0) for n in G.nodes()])
    return y_k


def initialize_y_k_topo(corner_graphs: Dict[str, nx.DiGraph], mode: str = "setup") -> Dict[str, np.ndarray]:
    """
    初始化每个 corner 的 y 向量（arrival time），基于拓扑传播。
    mode: 'setup'（最长路径）或 'hold'（最短路径）
    """
    assert mode in {"setup", "hold"}
    delay_attr = "setup_delay" if mode == "setup" else "hold_delay"
    y_k = {}

    for corner, G in corner_graphs.items():
        y_dict = {}
        cycles = list(nx.simple_cycles(G))
        for cycle in cycles:
            print("❗ Detected cycle:", cycle)
        for node in nx.topological_sort(G):
            preds = list(G.predecessors(node))
            if not preds:
                # 初始节点：PI 或 FF 的输出，delay 为 0
                y_dict[node] = 0.0
            else:
                if mode == "setup":
                    y_dict[node] = max(
                        y_dict[p] + float(G[p][node][delay_attr]) for p in preds
                    )
                else:  # hold
                    y_dict[node] = min(
                        y_dict[p] + float(G[p][node][delay_attr]) for p in preds
                    )
        # 把 node 的 y 向量按 G.nodes() 顺序转成 ndarray
        y_k[corner] = np.array([y_dict[n] for n in G.nodes()])
    return y_k

def initialize_y_shared(y_k: Dict[str, np.ndarray]) -> np.ndarray:
    return np.mean(list(y_k.values()), axis=0)

# 初始化 λ_k 为全0 拉格朗日乘子 为惩罚项
def initialize_lambda_k(y_k: Dict[str, np.ndarray]) -> Dict[str, np.ndarray]:
    """
    初始化每个 corner 的 dual variable λ_k 为 0 向量。
    """
    lambda_k = {}
    for corner, y in y_k.items():
        lambda_k[corner] = np.zeros_like(y)
    return lambda_k

def check_convergence(y_k: Dict[str, np.ndarray], y_shared: np.ndarray, tol: float = 1e-3) -> bool:
    return all(np.max(np.abs(y_k[corner] - y_shared)) < tol for corner in y_k)
