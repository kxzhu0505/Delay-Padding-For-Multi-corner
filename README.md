# Delay-Padding-For-Multi-corner

## Usage
1. **Basic Usage**
```python
from core.dual_decomposition import solve_dual_decomposition
from core.timing_analyzer import analyze_timing

# Create timing graph
graph = create_timing_graph()

# Run dual decomposition algorithm
y_k, y_shared = solve_dual_decomposition(
    graph=graph,
    corners=['ss_asap7', 'ff_asap7'],
    T_CLK=1.0  # clock period
)

# Analyze timing and generate padding solution
padding_solution = analyze_timing(graph, y_shared)
```

2. **Parameter Configuration**
- `T_CLK`: Clock period
- `tol`: Convergence tolerance
- `max_iter`: Maximum iterations
- `step_size`: Step size control parameter

## Optimization Results
- Supports timing convergence across multiple corners
- Automatically calculates optimal delay padding solutions
- Minimizes additional delay while ensuring timing convergence

## Important Notes
1. Setup violations cannot be fixed by delay padding, requiring:
   - Critical path optimization
   - Re-placement and routing
   - Clock frequency adjustment

2. Hold violations can be resolved through delay padding:
   - Tool automatically calculates required delay
   - Generates specific delay cell insertion plans

## Dependencies
- Python 3.6+
- cvxpy
- numpy
- networkx (for graph processing)

## Installation
```bash
git clone [repository_url]
cd DelayPadding
pip install -r requirements.txt
```

## Future Development
- [ ] Support for additional corner scenarios
- [ ] Algorithm convergence speed optimization
- [ ] GUI implementation
- [ ] Support for more timing constraint types
- [ ] Integration with standard EDA flow

## Algorithm Details
The tool implements a dual decomposition approach to solve the timing optimization problem:

1. **Problem Formulation**
```math
min_{y_k} ∑_{(u,v)∈E} λ_k[(u,v)] * (y_k[(u,v)] - y_shared[(u,v)])

subject to:
setup mode: 0 ≤ y_k[(u,v)] ≤ T_CLK + library_setup
hold mode: bounded_hold_time ≤ y_k[(u,v)] ≤ T_CLK
```

2. **Key Features**
- Step size control for stable convergence
- Normalized lambda updates
- Multi-corner coordination

## Performance
- Efficient convergence for practical circuit designs
- Scalable to large netlists
- Handles multiple timing constraints simultaneously

## Contributing
Contributions via Issues and Pull Requests are welcome.

## License
[Choose appropriate license]

## Contact
[Your contact information]

## Acknowledgments
Thanks to all developers who have contributed to this project.
