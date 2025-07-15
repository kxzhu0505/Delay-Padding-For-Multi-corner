import math
import numpy as np
import networkx as nx
from typing import Tuple
from typing import Dict
# from core.bf_solver import bellman_ford_solver
from core.lp_solver import solve_subproblem_lp
from core.utils import initialize_y_k, initialize_y_shared, initialize_lambda_k, check_convergence

def run_dual_delay_padding(corner_graphs: Dict[str, 'nx.DiGraph'], T_CLK: float, max_iter: int = 200, rho: float = 1):
    # Step 1: 初始化每个角的 y^(k)
    # setup analysis（longest delay path）
    y_k_setup = initialize_y_k(corner_graphs, mode="setup")
    
    # hold analysis（shortest delay path）
    y_k_hold = initialize_y_k(corner_graphs, mode="hold")
    # print(f"y_k_setup: {y_k_setup}")
    # print(f"y_k_hold: {y_k_hold}")

    # # Step 2: 初始化共享 y
    y_shared_setup = initialize_y_shared(y_k_setup)
    y_shared_hold = initialize_y_shared(y_k_hold)

    # print(f"y_shared_setup: {y_shared_setup}")
    # print(f"y_shared_hold: {y_shared_hold}")

    # # Step 3: 初始化 λ_k
    lambda_k_setup = initialize_lambda_k(y_k_setup)
    lambda_k_hold = initialize_lambda_k(y_k_hold)

    # print(f"lambda_k_setup: {lambda_k_setup}")
    # print(f"lambda_k_hold: {lambda_k_hold}")

    T_LOW = 0.1
    T_HIGH = T_CLK
    for iteration in range(max_iter):
        T_MID = (T_LOW + T_HIGH) / 2

        print(f"\n🔍 Iteration {iteration}: Trying T_CLK = {T_MID:.4f}")
        # Step 4: 进入主迭代
    
        # === Step 1: setup 模式下的 delay padding 求解 ===
        # 要使用同一个yshared来让不同的corner的arrival time都合法
        print("🔧 Solving for SETUP mode...")
        final_y_k_setup, final_y_shared_setup = dual_loop_solver_path_based(
            y_k=y_k_setup,
            y_shared=y_shared_setup,
            lambda_k=lambda_k_setup,
            corner_graphs=corner_graphs,
            T_CLK=T_MID,
            mode="setup"
        )

        # # === Step 2: hold 模式下的 delay padding 求解 ===
        # 要使用同一个yshared来让不同的corner的arrival time都合法
        print("🔧 Solving for HOLD mode...")
        final_y_k_hold, final_y_shared_hold = dual_loop_solver_path_based(
            y_k=y_k_hold,
            y_shared=y_shared_hold,
            lambda_k=lambda_k_hold,
            corner_graphs=corner_graphs,
            T_CLK=T_MID,
            mode="hold"
        )

        # 延迟填充
        
        setup_delay_patch = implement_delay_padding(final_y_shared_setup, corner_graphs["ss_asap7"], T_MID)
        hold_delay_patch = implement_delay_padding(final_y_shared_hold, corner_graphs["ff_asap7"], T_MID)

        # 验证延迟填充
        valid_setup = verify_patched_timing(final_y_shared_setup, corner_graphs["ss_asap7"], setup_delay_patch, T_MID)
        valid_hold = verify_patched_timing(final_y_shared_hold, corner_graphs["ff_asap7"], hold_delay_patch, T_MID)

        if valid_setup and valid_hold:
            T_HIGH = T_MID
        else:
            T_LOW = T_MID
        
        if abs(T_HIGH - T_LOW) < 1e-3:
            print(f"\n✅ Converged. Returning T_CLK = {T_HIGH:.4f}")
            return T_HIGH

    print(f"\n⚠️ Did not converge. Returning conservative T_CLK = {T_HIGH:.4f}")
    return T_HIGH

def dual_loop_solver_path_based(
    y_k: Dict[str, Dict[Tuple[str, str], float]],
    y_shared: Dict[Tuple[str, str], float],
    lambda_k: Dict[str, Dict[Tuple[str, str], float]],
    corner_graphs: Dict[str, any],
    T_CLK: float,
    mode: str = "setup",
    max_iter: int = 50,
    rho: float = 1.0,
    tol: float = 1e-3
):
    """
    Dual decomposition solver (path-based LP version).
    """
    
    for it in range(max_iter):
        print(f"\n🔁 Iteration {it} [{mode}]")

        # 1. solve subproblem per corner
        for corner in y_k:
            try:
                y_k[corner] = solve_subproblem_lp(T_CLK, corner, y_shared, lambda_k, corner_graphs[corner], mode=mode)
            except RuntimeError as e:
                print(str(e))
                continue

        # 2. update shared y
        all_edges = set(edge for ck in y_k.values() for edge in ck)
        new_y_shared = {
            edge: sum(y_k[c][edge] for c in y_k if edge in y_k[c]) / len([c for c in y_k if edge in y_k[c]])
            for edge in all_edges
        }

        # 3. check convergence
        # diff = max(abs(new_y_shared[e] - y_shared[e]) for e in new_y_shared if e in y_shared)
        # print(f"🔍 Max change in y_shared: {diff:.4f}")
        # if diff < tol:
        #     print("✅ Converged.")
        #     return y_k, new_y_shared
        if check_convergence(y_k, new_y_shared, y_shared):
            return y_k, new_y_shared
        

        y_shared = new_y_shared

        # method 1
        # 4. update lambda_k
        avg_deviation = {}
        for edge in y_shared:
            deviations = [y_k[corner][edge] - y_shared[edge] for corner in y_k]
            avg_deviation[edge] = sum(map(abs, deviations)) / len(deviations)
   
        for corner in y_k:
            for edge in y_k[corner]:
                # 根据偏差大小动态调整rho
                adaptive_rho = rho * (1.0 / (1.0 + avg_deviation[edge]))
                delta = y_k[corner][edge] - y_shared[edge]
                lambda_k[corner][edge] += adaptive_rho * delta
        # 4. update lambda_k
        # method 2
        # for corner in y_k:
        #     for edge in y_k[corner]:
        #         lambda_k[corner][edge] += rho * (y_k[corner][edge] - y_shared[edge])
        
        #method 3
        # for corner in y_k:
        #     for edge in y_k[corner]:
        #         # 归一化的更新
        #         delta = (y_k[corner][edge] - y_shared[edge]) / max(abs(y_shared[edge]), 1.0)
        #         lambda_k[corner][edge] += rho * delta


    print("⚠️ Reached max iterations without convergence.")
    return y_k, y_shared

def check_convergence(y_k, new_y_shared, y_shared, tol=1e-3, rel_tol=1e-2):
    # 1. 检查y_shared的变化
    abs_diff = max(abs(new_y_shared[e] - y_shared[e]) for e in new_y_shared if e in y_shared)
    rel_diff = max(
        abs(new_y_shared[e] - y_shared[e]) / max(abs(y_shared[e]), 1.0)
        for e in new_y_shared if e in y_shared
    )
    
    # 2. 检查所有corner是否都接近y_shared
    corner_diff = max(
        abs(y_k[corner][edge] - new_y_shared[edge]) / max(abs(new_y_shared[edge]), 1.0)
        for corner in y_k
        for edge in y_k[corner]
    )
    
    # 打印详细的收敛信息
    print(f"🔍 Absolute change in y_shared: {abs_diff:.4f}")
    print(f"🔍 Relative change in y_shared: {rel_diff:.4f}")
    print(f"🔍 Max corner deviation: {corner_diff:.4f}")
    
    # 同时满足三个条件才认为收敛
    is_converged = (abs_diff < tol) and (rel_diff < rel_tol) and (corner_diff <= 0.1)
    
    if is_converged:
        print("✅ Converged.")
    
    return is_converged


def implement_delay_padding(y_shared: Dict[Tuple[str, str], float], 
                            graph: nx.DiGraph,
                            T_CLK: float,
                            tol: float = 1e-3):
    """
    根据共享 delay（y_shared）与时钟周期，对图中的边插入必要的 delay 以满足 setup/hold。
    """
    delay_patch = {}  # {(u, v): delay_to_add}

    for u, v in graph.edges():
        y = y_shared.get((u, v), None)
        if y is None:
            continue  # skip if no y_shared for this edge

        # Get setup & hold library constraints
        setup_info = graph[u][v].get('setup_delay', {})
        hold_info  = graph[u][v].get('hold_delay', {})
        setup_time = setup_info.get('library_time', None)
        hold_time  = hold_info.get('library_time', None)

        if setup_time is None or hold_time is None:
            continue  # skip if missing info

        required_max = T_CLK + setup_time
        required_min = max(hold_time, 0.0)

        padding = 0.0

        # Setup violation: arrival too late
        if y > required_max:
            pad = y - required_max
            print(f"⚠️ Setup violation on edge {u}->{v}: arrival={y:.2f} > {required_max:.2f}, pad={pad:.2f}")
            padding = max(padding, pad)

        # Hold violation: arrival too early
        if y < required_min:
            pad = required_min - y
            print(f"⚠️ Hold violation on edge {u}->{v}: arrival={y:.2f} < {required_min:.2f}, pad={pad:.2f}")
            padding = max(padding, pad)

        if padding > 0:
            delay_patch[(u, v)] = padding

    return delay_patch

def verify_patched_timing(y_shared: Dict[Tuple[str, str], float],
                          graph: nx.DiGraph,
                          delay_patch: Dict[Tuple[str, str], float],
                          T_CLK: float,
                          tol: float = 1e-3) -> bool:
    """
    验证应用 delay patch 后，所有 setup/hold 约束是否满足
    """
    all_passed = True

    for u, v in graph.edges():
        y = y_shared.get((u, v), None)
        if y is None:
            continue

        patch = delay_patch.get((u, v), 0.0)
        y_patched = y - patch
        # 注意这里是 + 还是 -

        # 获取 library 约束
        setup_time = graph[u][v]['setup_delay'].get('library_time', None)
        hold_time  = graph[u][v]['hold_delay'].get('library_time', None)
        if setup_time is None or hold_time is None:
            continue

        required_max = T_CLK + setup_time
        required_min = hold_time

        # 检查 setup violation
        if y_patched > required_max:
            print(f"❌ Setup FAIL: {u}->{v}, patched_y = {y_patched:.2f} > {required_max:.2f}")
            all_passed = False

        # 检查 hold violation
        if y_patched < required_min:
            print(f"❌ Hold FAIL: {u}->{v}, patched_y = {y_patched:.2f} < {required_min:.2f}")
            all_passed = False

    if all_passed:
        print("✅ All timing constraints met after delay padding.")
    else:
        print("❌ Timing violations remain after delay padding.")
    
    return all_passed

