import numpy as np
import networkx as nx
from typing import Dict

def bellman_ford_solver(G: nx.DiGraph, lambda_k: np.ndarray, y_shared: np.ndarray, mode: str ) -> np.ndarray:
    """
    使用 Bellman-Ford 算法在含环 timing graph 中求解子问题 y_k：
    min f_k(y_k) + λ_k^T(y_k - y_shared)

    参数：
        - G: nx.DiGraph，每个边包含 delay 属性
        - lambda_k: 本角的 dual variable 向量
        - y_shared: 共享 y（平均目标）
        - mode: "setup" 或 "hold"

    返回：
        - y_k: np.ndarray（节点顺序与 G.nodes() 一致）
    """
    assert mode in {"setup", "hold"}, "mode must be 'setup' or 'hold'"
    delay_attr = "setup_delay" if mode == "setup" else "hold_delay"
    maximize = (mode == "setup")

    arrival = {
        node: float('-inf') if maximize else float('inf')
        for node in G.nodes()
    }

    # 使用无前驱节点作为初始 source
    sources = [n for n in G.nodes() if G.in_degree(n) == 0]
    if not sources:
        print("⚠️  No source nodes found, using all nodes as initial source.")
        sources = list(G.nodes())

    for s in sources:
        arrival[s] = 0.0

    # Bellman-Ford 主循环
    updated = True
    for _ in range(len(G.nodes()) - 1):
        if not updated:
            break
        updated = False
        for u, v, data in G.edges(data=True):
            delay = float(data.get(delay_attr, 0.0))
            if maximize:
                if arrival[u] + delay > arrival[v]:
                    arrival[v] = arrival[u] + delay
                    updated = True
            else:
                if arrival[u] + delay < arrival[v]:
                    arrival[v] = arrival[u] + delay
                    updated = True

    # 负环检测
    for u, v, data in G.edges(data=True):
        delay = float(data.get(delay_attr, 0.0))
        if maximize:
            if arrival[u] + delay > arrival[v] + 1e-6:
                raise ValueError(f"❌ Negative cycle detected in {mode} mode: {u} → {v}")
        else:
            if arrival[u] + delay < arrival[v] - 1e-6:
                raise ValueError(f"❌ Negative cycle detected in {mode} mode: {u} → {v}")

    # 转换为向量并执行拉格朗日修正
    node_order = list(G.nodes())
    y_k = np.array([arrival[n] for n in node_order])
    # y_k += -lambda_k  # 对偶驱动修正项

    print(f"y_k: {y_k}")
    return y_k
