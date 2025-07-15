import numpy as np
from typing import Dict
import networkx as nx
from typing import Tuple

def initialize_y_k(corner_graphs, mode: str = "setup") -> Dict[Tuple[str, str], float]:
    """
    从单个 corner 的图 G 中初始化 y_k（边上的 delay），根据 mode 区分 setup/hold。

    参数:
        G    : 单个 corner 的 nx.DiGraph
        mode : "setup" 使用 delay_max，"hold" 使用 delay_min

    返回:
        Dict[(u, v)] → delay
    """
    

    assert mode in {"setup", "hold"}
    attr = "setup_delay" if mode == "setup" else "hold_delay"

    y_k = {}
    for corner, G in corner_graphs.items():
        y_dict = {}
        for u, v, data in G.edges(data=True):
            delay_dict = data.get(attr, {})
            arrival = delay_dict.get("arrival_time", {})
            setup_library = delay_dict.get("library_time", {})
            if isinstance(arrival, (int, float)):  # 若直接是 delay（非字典）
                y_dict[(u, v)] = arrival
            elif isinstance(delay_dict, dict):
                print(f"⚠️ Expected scalar delay in graph edge {u}→{v}, but got dict.")
            else:
                print(f"⚠️ Missing {attr} for edge {u} → {v}")
        y_k[corner] = y_dict
    return y_k


def initialize_y_shared(y_k_all_corners: Dict[str, Dict[Tuple[str, str], float]]) -> Dict[Tuple[str, str], float]:
    """
    初始化 y_shared 为所有 corner 上每条边 delay 的平均值。
    
    参数:
        y_k_all_corners: Dict[corner][(u,v)] = arrival_time

    返回:
        y_shared[(u,v)] = average_arrival
    """
    from collections import defaultdict

    edge_values = defaultdict(list)

    # 收集所有 corner 上每条边的 delay
    for corner, y_k in y_k_all_corners.items():
        for edge, val in y_k.items():
            edge_values[edge].append(val)

    # 求平均
    y_shared = { edge: sum(vals)/len(vals) for edge, vals in edge_values.items() }

    return y_shared


def initialize_lambda_k(y_k_all_corners: Dict[str, Dict[Tuple[str, str], float]]) -> Dict[str, Dict[Tuple[str, str], float]]:
    """
    初始化 lambda_k 为所有 corner 和边上的 λ = 0

    参数:
        y_k_all_corners: Dict[corner][(u,v)] = arrival_time

    返回:
        lambda_k[corner][(u,v)] = 0.0
    """
    lambda_k = {}
    for corner, y_k in y_k_all_corners.items():
        lambda_k[corner] = { edge: 0.0 for edge in y_k.keys() }
    return lambda_k


def check_convergence(y_k: Dict[str, np.ndarray], y_shared: np.ndarray, tol: float = 1e-3) -> bool:
    return all(np.max(np.abs(y_k[corner] - y_shared)) < tol for corner in y_k)
