import cvxpy as cp
import numpy as np
from typing import Dict, Tuple

def solve_subproblem_lp(
    T_CLK: float,
    corner: str,
    y_shared: Dict[Tuple[str, str], float],
    lambda_k: Dict[str, Dict[Tuple[str, str], float]],
    graph,
    mode: str = "setup",
) -> Dict[Tuple[str, str], float]:
    """
    用 LP 求解 corner k 的子问题
    变量: y_k[(u,v)]
    目标: min ∑ λ_k[(u,v)] * (y_k - y_shared)
    约束: y_k[(u,v)] <= required_time (setup) or >= (hold)
    """
    assert mode in {"setup", "hold"}
    var = {}
    constraints = []
    HOLD_TIME_EPSILON = 0.0
    STEP_SIZE = 0.1
    
    for u, v, data in graph.edges(data=True):
        edge = (u, v)
        var[edge] = cp.Variable()

        if edge in y_shared:
            constraints.append(var[edge] - y_shared[edge] <= STEP_SIZE * abs(y_shared[edge]))
            constraints.append(var[edge] - y_shared[edge] >= -STEP_SIZE * abs(y_shared[edge]))

        library_setup = data.get(mode + "_delay", {}).get("library_time", None)
        if mode == "setup":
            library_setup = float(data.get("setup_delay", {}).get("library_time", None))
            if library_setup is not None:
                required_time = T_CLK + library_setup
        else:
            required_time = float(data.get("hold_delay", {}).get("library_time", None))
            bounded_hold_time = max(required_time, HOLD_TIME_EPSILON)
        if required_time is not None:
            if mode == "setup":
                constraints.append(var[edge] <= required_time)
                constraints.append(var[edge] >= 0)
            else:
                constraints.append(var[edge] >= bounded_hold_time)
                constraints.append(var[edge] <= T_CLK)
        else:
            print(f"❌ No required time found for edge {edge} in corner {corner}")

    for edge in var:
        print(f"🔍 [corner {corner}] edge {edge} | λ_k = {lambda_k[corner][edge]:.3f} | y_shared = {y_shared[edge]:.3f}")

    # 构建目标函数
    objective = cp.Minimize(cp.sum([
        lambda_k[corner][e] * (var[e] - y_shared[e])
        for e in var
    ]))

    prob = cp.Problem(objective, constraints)
    prob.solve(solver=cp.ECOS)

    if prob.status not in ["optimal", "optimal_inaccurate"]:
        raise RuntimeError(f"❌ LP solver failed for corner {corner}: {prob.status}")

    return {e: var[e].value for e in var}

