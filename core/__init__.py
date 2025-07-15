"""
Delay Padding项目核心模块

包含以下主要功能：
1. TimingGraphBuilder: 构建和修改timing constraint graphs
2. NegativeCycleDetector: 负环检测和最小可行时钟周期分析
3. DualDecompositionSolver: 多工艺角delay padding优化 (基于拉格朗日对偶分解)

主要功能：
- 构建多工艺角timing constraint graphs
- 检测setup和hold时序约束的负环
- 计算最小可行时钟周期
- 比较修改前后的性能差异
- 多工艺角delay padding优化，获得跨工艺角一致的解决方案
"""

from .graph_builder import TimingGraphBuilder, create_timing_graphs
from .negative_cycle_detector import (
    NegativeCycleDetector, 
    analyze_timing_graphs,
    compare_before_after_modification,
    quick_before_after_comparison_example,
    multi_corner_delay_padding_optimization,
    demo_dual_decomposition_optimization
)
from .dual_decomposition import (
    DualDecompositionSolver, 
    run_dual_decomposition_optimization
)

__all__ = [
    # Graph Builder
    'TimingGraphBuilder',
    'create_timing_graphs',
    
    # Negative Cycle Detection
    'NegativeCycleDetector',
    'analyze_timing_graphs', 
    'compare_before_after_modification',
    'quick_before_after_comparison_example',
    
    # Dual Decomposition Optimization
    'DualDecompositionSolver',
    'run_dual_decomposition_optimization',
    'multi_corner_delay_padding_optimization',
    'demo_dual_decomposition_optimization'
] 