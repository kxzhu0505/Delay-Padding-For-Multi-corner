# Multi-Corner Delay Padding Optimization System

A multi-corner timing constraint graph optimization solution based on Lagrangian Dual Decomposition.

## 🎯 System Overview

This system solves the delay padding optimization problem in multi-corner environments, aiming to find a **consistent delay padding solution across all corners** that ensures each corner meets timing constraints.

### Core Concepts

1. **Modified Timing Constraint Graph**: Insert nodes us, uh into the original graph based on path dependencies
2. **Clock Skew Scheduling**: Solve A'·u' = y' for the modified graph
3. **Delay Padding Optimization**: Use dual decomposition to find consistent delay padding solutions
4. **Constraint Satisfaction**: Ensure all corners have no negative cycles after applying delay padding

## 📁 File Structure

```
core/
├── graph_builder.py           # Build and modify timing constraint graphs
├── negative_cycle_detector.py # Negative cycle detection and optimization integration
├── dual_decomposition.py      # Lagrangian dual decomposition algorithm
└── __init__.py               # Module import configuration
```

## 🚀 Quick Start

### 1. Basic Usage

```python
from core import TimingGraphBuilder, multi_corner_delay_padding_optimization

# Configure corners and file paths
corners_config = {
    'ss_asap7': ['path/to/ss_lib.lib'],
    'ff_asap7': ['path/to/ff_lib.lib']
}

# Build timing graphs
builder = TimingGraphBuilder('netlist.v', corners_config, work_dir='./output')
builder.build_timing_graphs()

# Run multi-corner optimization
results = multi_corner_delay_padding_optimization(
    builder=builder,
    T_clk=None,  # Automatically find minimum feasible clock period
    output_dir='./output'
)

if results['success']:
    print(f"✅ Optimization successful! Total delay padding: {results['total_padding']:.3f}")
    print(f"📈 Modified edges: {results['modified_edges']}")
    print(f"🎯 Final feasible: {results['final_feasible']}")
```

### 2. Command Line Usage

```bash
# Run full test
python core/negative_cycle_detector.py

# Run quick demo  
python core/negative_cycle_detector.py demo

# Run dual decomposition optimization demo
python core/negative_cycle_detector.py dual
```

## 🔧 Algorithm Details

### Correct Dual Decomposition Formulation

In the modified timing constraint graphs, we solve:

```
min  Σ |u_s^k - u_s^shared| + Σ |u_h^k - u_h^shared|    (minimize consistency violation)
{u^k}

s.t. For each corner k:
     - Modified graph has no setup negative cycles: A'^k · u^k = y^k, no setup negative cycles
     - Modified graph has no hold negative cycles: A'^k · u^k = y^k, no hold negative cycles
     - Consistency constraints: u_s^k ≈ u_s^shared, u_h^k ≈ u_h^shared
```

Where:
- **u^k**: Node potentials for corner k (including original nodes and inserted us, uh nodes)
- **u_s^shared, u_h^shared**: Shared inserted node potentials across all corners
- **delay padding = u_s - u_original or u_h - u_original**

### Key Insights

1. **Delay padding is implicit in node potentials**:
   - No need to explicitly maintain delay padding variables
   - The potential values of us, uh nodes represent delay padding effects

2. **Consistency constraints**:
   - All corners should have consistent us, uh node potentials
   - Ensures unified delay padding across corners

3. **Feasibility constraints**:
   - Each corner's modified graph should have no negative cycles
   - Achieved through node potential solving

### Algorithm Flow

1. **Initialization**: 
   - Identify original nodes and inserted nodes (us, uh)
   - Initialize node potentials for each corner
   - Initialize Lagrangian multipliers (for consistency constraints on inserted nodes)

2. **Iterative Optimization**:
   - **Update node potentials**: Adjust inserted node potentials based on Lagrangian multipliers and consistency constraints
   - **Update Lagrangian multipliers**: Adjust based on feasibility and consistency violation levels
   - **Check convergence**: Monitor changes in node potentials and multipliers

3. **Convergence Criteria**:
   - Node potential changes < tolerance
   - Lagrangian multiplier changes < tolerance

4. **Solution Extraction**:
   - delay padding = u_s^shared - u_original
   - Verify feasibility across all corners

## 📊 Output Files

### Main Result Files

1. **`dual_decomposition_results.txt`**: Main optimization results
   - Clock period and convergence status  
   - Delay padding solution details
   - Shared potentials for inserted nodes
   - Node potential solutions (by corner)
   - Feasibility status for each corner

2. **`convergence_history.txt`**: Convergence history
   - Objective function value for each iteration
   - Consistency violation levels
   - Number of infeasible corners

### Graph Information Files

3. **`modified_graph_{corner}.txt`**: Modified graph structure
4. **`edge_type_stat_{corner}.txt`**: Edge type statistics

## 🎛️ Parameter Configuration

### TimingGraphBuilder Parameters

```python
builder = TimingGraphBuilder(
    netlist_path='path/to/netlist.v',     # Verilog netlist file
    corners_config={                       # Corner configuration
        'corner_name': ['lib_file_path']
    },
    work_dir='./output'                   # Working directory
)
```

### Dual Decomposition Parameters

```python
optimization_results = run_dual_decomposition_optimization(
    corner_graphs=modified_graphs,        # Modified graphs
    T_clk=target_clock_period,           # Clock period
    max_iterations=1000,                 # Maximum iterations
    tolerance=1e-4,                      # Convergence tolerance
    step_size_u=0.01,                    # Node potential update step size
    step_size_lambda=0.01                # Lagrangian multiplier update step size
)
```

## 📈 Result Interpretation

### Success Indicators

- **Convergence status**: `converged = True`
- **All corners feasible**: `all_feasible = True`  
- **Reasonable delay padding**: Total amount not excessive, moderate number of modified edges

### Failure Cases

1. **Algorithm doesn't converge**: Adjust step size parameters or increase iterations
2. **Some corners infeasible**: May need larger clock period
3. **Excessive delay padding**: Check if timing constraints are reasonable

## 🔍 Debugging Tips

### View Detailed Information

```python
# Print optimization process details
print(f"Convergence status: {results['converged']}")
print(f"Iterations: {results['iterations']}")
print(f"Total delay padding: {sum(results['delay_padding_solution'].values())}")

# View feasibility for each corner
for corner, feasible in results['final_feasibility'].items():
    print(f"{corner}: {'✅' if feasible else '❌'}")

# View shared potentials for inserted nodes
for node, potential in results['shared_potentials'].items():
    print(f"Shared potential {node}: {potential:.6f}")
```

### Analyze Convergence History

```python
history = results['convergence_history']
for record in history[-5:]:  # View last 5 iterations
    print(f"Iteration {record['iteration']}: "
          f"consistency_violation={record['consistency_violation']:.3f}, "
          f"infeasible_corners={record['infeasible_corners']}")
```

### Analyze Node Potentials

```python
# View node potential differences across corners
node_potentials = results['node_potentials']
shared_potentials = results['shared_potentials']

for node in shared_potentials:
    print(f"\nNode {node}:")
    print(f"  Shared potential: {shared_potentials[node]:.6f}")
    for corner in node_potentials:
        corner_potential = node_potentials[corner][node]
        diff = abs(corner_potential - shared_potentials[node])
        print(f"  {corner}: {corner_potential:.6f} (difference: {diff:.6f})")
```

## ⚠️ Important Notes

1. **Corner data**: Ensure timing data for all corners is correct
2. **Clock period**: If all corners are infeasible, try increasing clock period
3. **Convergence**: If not converging, adjust step size parameters
4. **Memory usage**: Large designs may require significant memory

## 🎓 Related Papers

- "Clock Skew Scheduling for Timing Constraint Graphs"
- "Lagrangian Dual Decomposition for Multi-Corner Optimization"  
- "Delay Padding in VLSI Timing Optimization"

## 📞 Technical Support

If you encounter issues, please check:
1. Log files in the output directory
2. Convergence curves in `convergence_history.txt`
3. Feasibility status for each corner

---
*Last updated: 2024* 
