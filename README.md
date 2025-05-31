# DelayPaddingPVT

## Project Overview

**DelayPaddingPVT** is a tool for statistical static timing analysis (SSTA) and delay padding optimization under multiple process-voltage-temperature (PVT) corners for digital circuits. It supports modeling each edge delay as a Generalized Extreme Value (GEV) distribution, enabling robust timing analysis and optimization under process variations. The tool can automatically insert delay padding to maximize the probability of timing closure and supports searching for the minimum clock period that meets a user-specified yield (probability) constraint.

## Key Features

- **Multi-corner Timing Graph Construction**: Automatically parses netlists and Liberty files for different PVT corners and builds timing graphs.
- **SSTA Support**: Each edge delay can be modeled as a GEV distribution `(c, loc, scale)`, enabling statistical analysis.
- **Probability-constrained Optimization**: Specify a target yield η (e.g., 0.95), and the tool will optimize delay padding so that the probability of timing closure exceeds η, or search for the minimum clock period that meets this constraint.
- **Negative Cycle Detection and Repair**: Detects and repairs setup/hold negative cycles using delay padding.
- **Automated Script and Report Generation**: Generates OpenSTA scripts, parses timing reports, and supports custom path analysis.

## Directory Structure

```
DelayPaddingPVT/
├── main.py                # Project entry point and usage example
├── core/
│   ├── graph_builder.py   # Timing graph construction and report parsing (SSTA support)
│   ├── dual_decomposition.py # Main multi-corner delay padding optimization algorithm
│   ├── lp_solver.py       # LP solver for optimization
│   ├── cp_optimize.py     # Minimum clock period search
│   ├── run_ssta.py        # SSTA analysis utilities
│   ├── utils.py           # Utility functions
│   └── bf_solver.py       # Bellman-Ford negative cycle detection
├── platform/              # Liberty files for different PVT corners
├── gcd_dir/               # Example netlist, timing reports, and OpenSTA scripts
```

## Requirements

- Python 3.7+
- [networkx](https://networkx.org/)
- [scipy](https://scipy.org/) (for GEV distribution modeling)
- OpenSTA (for timing analysis; must be installed and in your PATH)

Install Python dependencies:
```bash
pip install networkx scipy
```

## Quick Start

1. **Prepare Netlist and Liberty Files**  
   Place your Verilog netlist and Liberty files for each PVT corner in the appropriate directories.

2. **Configure `main.py`**  
   Edit `netlist_path` and `corners_config` in `main.py` to point to your netlist and Liberty files.

3. **Run the Main Program**  
   ```bash
   python main.py
   ```
   The program will automatically build timing graphs for all corners, perform SSTA and delay padding optimization, and output the minimum feasible clock period and padding results.

## SSTA and GEV Distribution Support

- Each edge delay can be described by GEV parameters `(c, loc, scale)`, stored in the `gev_params` field of `setup_delay`/`hold_delay`.
- The optimization algorithm uses `scipy.stats.genextreme` to compute quantiles (ppf) for the specified yield η, converting the probability constraint into an equivalent timing constraint.
- You can set the target yield η in `main.py` (e.g., `eta=0.95` for 95% yield).

## Main Interfaces

- `TimingGraphBuilder`: Automatically builds multi-corner timing graphs with SSTA support.
- `run_dual_delay_padding`: Main entry for multi-corner delay padding optimization with probability constraints.
- `find_min_TCLK`: Searches for the minimum clock period that meets the probability constraint.

## Example Output

```
Minimum feasible clock period at 95.0% yield: 512.345ns
Optimal node potentials: {...}
Setup padding: {...}
Hold padding: {...}
Info: Converged successfully.
```

## Acknowledgements

- This project leverages OpenSTA, networkx, scipy, and other open-source tools.
- Example Liberty files are based on ASAP7.

