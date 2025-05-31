from core.dual_decomposition import run_dual_delay_padding

def find_min_TCLK(corner_graphs, TCLK_min, TCLK_max, eta, tol=0.1, max_attempts=50):
    """
    二分查找最小可行的时钟周期
    
    参数:
        corner_graphs: 多Corner时序图
        TCLK_min: 最小时钟周期
        TCLK_max: 最大时钟周期
        tol: 收敛阈值
        max_attempts: 最大尝试次数
    
    返回:
        float: 最小可行时钟周期
        dict: 最优电势解
        dict: 最优setup padding解
        dict: 最优hold padding解
        str: 信息
    """
    # 记录最后一次成功的结果
    last_success = None
    attempts = 0
    
    # 首先验证TCLK_max是否可行
    p, setup_padding, hold_padding, converged, msg = run_dual_delay_padding(corner_graphs, TCLK_max, eta)
    if not converged:
        return None, None, None, None, f"在最大时钟周期{TCLK_max}下仍无法找到可行解，错误信息：{msg}"
    else:
        last_success = (TCLK_max, p, setup_padding, hold_padding)
    
    while TCLK_max - TCLK_min > tol and attempts < max_attempts:
        attempts += 1
        mid_TCLK = (TCLK_min + TCLK_max) / 2
        p, setup_padding, hold_padding, converged, msg = run_dual_delay_padding(corner_graphs, mid_TCLK, eta)
        
        if converged:
            # 当前周期可行，尝试更小的周期
            TCLK_max = mid_TCLK
            last_success = (mid_TCLK, p, setup_padding, hold_padding)
        else:
            # 当前周期不可行，尝试更大的周期
            TCLK_min = mid_TCLK
            print(f"TCLK = {mid_TCLK:.3f}ns 不可行，原因：{msg}")
    
    if last_success is None:
        return None, None, None, None, "未找到可行解"
    
    TCLK_opt, p_optimal, setup_optimal, hold_optimal = last_success
    
    # 检查是否因为达到最大尝试次数而退出
    if attempts >= max_attempts:
        return TCLK_opt, p_optimal, setup_optimal, hold_optimal, f"达到最大尝试次数({max_attempts})，返回最后一个可行解"
    
    return TCLK_opt, p_optimal, setup_optimal, hold_optimal, "找到最优解"