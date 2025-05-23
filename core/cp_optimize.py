from core.dual_decomposition import run_dual_delay_padding
def find_minimum_tclk(corner_graphs,
                      initial_tclk_high: float,
                      tol: float = 1e-2,
                      max_iters: int = 20,
                      verbose: bool = True) -> float:
    """
    二分法寻找最小 T_CLK，使得所有 corner 下 delay padding 都可以满足 setup/hold 时序。

    参数:
        corner_graphs: 多个 corner 的 nx.DiGraph
        initial_tclk_high: 初始最大 T_CLK
        tol: 收敛精度
        max_iters: 最大迭代次数

    返回:
        最小合法 T_CLK
    """

    T_low = 0.1  # 设置一个很小的下限
    T_high = initial_tclk_high

    for iteration in range(max_iters):
        T_mid = (T_low + T_high) / 2

        if verbose:
            print(f"\n🔍 Iteration {iteration}: Trying T_CLK = {T_mid:.4f}")

        # Dual decomposition 解出共享 y
        y_shared, _, _ = run_dual_delay_padding(corner_graphs, T_CLK=T_mid, verbose=False)

        # 生成 delay patch
        G_rep = list(corner_graphs.values())[0]  # 任选一个 corner 用来 patch
        delay_patch = implement_delay_padding(y_shared, G_rep, T_mid)

        # 验证 patch 后是否 timing-legal（可实现）
        is_valid = check_feasibility(y_shared, G_rep, T_CLK=T_mid, tol=tol)

        if is_valid:
            T_high = T_mid
            if verbose:
                print(f"✅ T_CLK = {T_mid:.4f} is feasible.")
        else:
            T_low = T_mid
            if verbose:
                print(f"❌ T_CLK = {T_mid:.4f} is too tight.")

        if abs(T_high - T_low) < tol:
            print(f"\n🎯 Converged to minimum feasible T_CLK = {T_high:.4f}")
            return T_high

    print(f"\n⚠️ Did not converge. Returning conservative T_CLK = {T_high:.4f}")
    return T_high
