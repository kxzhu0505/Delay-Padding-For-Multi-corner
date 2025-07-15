# 多工艺角负环检测和最小可行时钟周期分析系统

## 概述

这个系统实现了多工艺角(multi-corner)timing constraint graph的负环检测和最小可行时钟周期分析。系统能够：

1. 构建原始timing graphs
2. 根据路径类型修改timing constraint graph
3. 检测setup和hold负环
4. 计算最小可行时钟周期
5. 分析特定时钟周期下的可行性

## 系统架构

```
core/
├── graph_builder.py           # 主要的图构建和修改功能
├── negative_cycle_detector.py # 负环检测和分析功能
├── dual_decomposition.py      # 双分解优化算法
├── example_usage.py           # 使用示例
└── __init__.py               # 模块导入配置
```

## 核心组件

### 1. TimingGraphBuilder

负责构建和修改timing constraint graph：

- **构建原始图**: 从Verilog网表和Liberty文件构建timing graph
- **边分类**: 根据setup/hold路径关系将边分为4类(a,b,c,d)
- **图修改**: 根据边类型添加相应的节点和重新分配延迟

### 2. NegativeCycleDetector

负责负环检测和最小可行时钟周期分析：

- **负环检测**: 使用Bellman-Ford算法检测setup和hold负环
- **二分搜索**: 找到最小可行时钟周期
- **多工艺角支持**: 同时考虑所有工艺角的约束

## 边的四种类型

根据您提供的图片，系统将timing constraint graph的边分为四种类型：

### 类型 'a': 无延迟可插入
- 不添加任何节点
- 保持原边不变
- 无法通过delay padding优化

### 类型 'b': ps、ph独立
- 添加两个独立节点: `us`(setup) 和 `uh`(hold)
- 原边 `u->v` 变为: `u->us->v` 和 `u->uh->v`
- 延迟分配: `u->us`和`u->uh`为0，`us->v`和`uh->v`为原约束

### 类型 'c': ps = ph
- 添加一个共同节点: `us`
- 原边 `u->v` 变为: `u->us->v`
- 延迟分配: `u->us`为0，`us->v`为原约束

### 类型 'd': ps >= ph
- 添加两个节点: `us`(setup主导) 和 `uh`(hold依赖)
- hold路径经过setup节点: `u->uh->us->v`
- 延迟分配: `u->us`和`u->uh`为0，其他边为原约束

## 使用方法

### 基本使用

```python
from core import create_timing_graphs

# 1. 构建timing graphs
builder = create_timing_graphs(
    netlist_path="path/to/netlist.v",
    corners_config={
        'ss_corner': ['ss_lib1.lib', 'ss_lib2.lib'],
        'ff_corner': ['ff_lib1.lib', 'ff_lib2.lib']
    },
    work_dir="output_directory"
)

# 2. 分析负环和最小可行时钟周期
detector = analyze_timing_graphs(
    corner_graphs=modified_graphs,
    T_clk_min=1.0,
    T_clk_max=20.0,
    precision=0.1
)

# 3. 检查特定时钟周期的可行性
results = detector.analyze_negative_cycles_at_period(T_clk=10.0)
```

### 修改前后比较分析 🆕

这是系统的核心功能之一，用于评估图修改策略的效果：

```python
from core import compare_before_after_modification, create_timing_graphs

# 1. 构建timing graphs
builder = create_timing_graphs(netlist_path, corners_config, work_dir)

# 2. 比较修改前后的可行时钟周期差距
comparison_results = compare_before_after_modification(
    builder=builder,
    T_clk_min=1.0,
    T_clk_max=500.0,
    precision=0.1,
    output_dir=work_dir
)

# 3. 查看比较结果
if comparison_results['improvement']:
    print(f"性能提升: {comparison_results['improvement']['percentage']:.1f}%")
elif comparison_results['degradation']:
    print(f"性能下降: {comparison_results['degradation']['percentage']:.1f}%")
```

### 快速演示

```python
from core import quick_before_after_comparison_example

# 运行快速演示
quick_before_after_comparison_example()
```

### 高级使用

```python
from core import NegativeCycleDetector, analyze_timing_graphs

# 直接使用NegativeCycleDetector
detector = NegativeCycleDetector(modified_graphs)

# 分析特定时钟周期（静默模式）
results = detector.analyze_negative_cycles_at_period_silent(T_clk=5.0)

# 完整的分析流程
detector = analyze_timing_graphs(
    corner_graphs=modified_graphs,
    T_clk_min=0.5,
    T_clk_max=50.0,
    precision=0.01,
    output_dir="results/"
)
```

## 输出文件

系统会生成以下输出文件：

1. **边类型统计**: `edge_type_stat_{corner}.txt`
   - 每条边的类型分类结果

2. **修改后的图信息**: `modified_graph_{corner}.txt`
   - 修改后的节点和边信息

3. **负环分析结果**: `negative_cycle_analysis.txt`
   - 详细的负环检测和最小可行时钟周期分析结果

4. **修改前后比较分析**: `before_after_comparison.txt` 🆕
   - 原始图vs修改后图的可行时钟周期比较
   - 性能提升/下降的定量分析
   - 按工艺角的详细比较结果

## 算法特点

### 负环检测
- 使用Bellman-Ford算法，时间复杂度O(VE)
- 分别检测setup和hold约束的负环
- 支持多工艺角并发分析

### 最小可行时钟周期计算
- 使用二分搜索，效率高
- 考虑所有工艺角的约束
- 可配置搜索范围和精度

### 图修改策略
- 根据路径依赖关系智能添加节点
- 正确分配延迟约束
- 保持时序语义的完整性

## 运行示例

```bash
# 运行完整的分析流程
cd /path/to/DelayPadding/core
python example_usage.py

# 运行基本测试
python graph_builder.py

# 运行负环检测和比较测试（完整版）
python negative_cycle_detector.py

# 运行快速比较演示
python negative_cycle_detector.py demo
```

## 配置说明

### 工艺角配置
```python
corners_config = {
    'corner_name': ['lib1.lib', 'lib2.lib', ...],
    # 支持多个工艺角
}
```

### 分析参数
- `T_clk_min`: 最小搜索时钟周期
- `T_clk_max`: 最大搜索时钟周期  
- `precision`: 搜索精度
- `work_dir`: 输出目录

## 故障排除

### 常见问题

1. **图构建失败**
   - 检查网表文件和Liberty文件路径
   - 确保OpenSTA工具可用

2. **负环检测失败**
   - 检查timing graph是否正确构建
   - 确认工艺角配置正确

3. **找不到可行时钟周期**
   - 扩大搜索范围
   - 检查时序约束是否过于严格

### 调试建议

1. 启用详细日志输出
2. 检查中间输出文件
3. 验证timing graph的节点和边信息
4. 测试单个工艺角的分析

## 依赖项

- Python 3.6+
- NetworkX
- OpenSTA (用于时序分析)
- NumPy (可选，用于数值计算)

## 扩展功能

系统设计为可扩展的架构，支持：

- 添加新的边类型处理策略
- 集成其他时序分析工具
- 支持更多的工艺角类型
- 添加可视化功能

## 性能考虑

- 大规模设计可能需要较长的分析时间
- 建议使用并行处理多个工艺角
- 可以调整搜索精度平衡速度和准确性

## 技术支持

如果遇到问题，请检查：
1. 输出日志文件
2. 中间结果文件
3. 工艺角配置的正确性
4. 时序约束的合理性 