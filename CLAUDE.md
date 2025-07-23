# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a biogas plant simulation written in Python that models the anaerobic digestion process. The simulation tracks feedstock through multiple stages: feeding, mixing, digestion, pasteurization, and separation.

## Development Commands

### Running the Simulation
```bash
python model.py
```

### Configuration GUI
```bash
python config_gui.py
```

The GUI provides an interactive interface to configure simulation parameters before running.

### Installing Dependencies
```bash
pip install -r requirements.txt
```

### Running Tests
```bash
~/.cache/uv/environments-v2/model-2d8ad278febad234/bin/python -m unittest test_model -v
```

## Architecture

The simulation follows a sequential process model:

### Core Components

- **FeedStock dataclass**: Represents different organic materials with properties like quantity, dry matter percentage, volatile solids percentage, gas yield, methane percentage, and digestion reduction factor.

- **Shit class**: The main container that holds all feedstock materials and provides statistical analysis. Despite the unconventional name, this is the core data structure that tracks material composition throughout the process.

### Process Flow

1. **Initial Feed** (`initial_feed()`): Loads feedstock data from `feed.csv`
2. **Mix** (`mix()`): Adds recirculation fluid and clean water
3. **Digest** (`digest()`): Converts organic matter to methane, mutates feedstock properties
4. **Pasteurize** (`pasteurize()`): Currently a placeholder function
5. **Separate** (`separate()`): Performs liquid-sludge separation

### Data Flow

- Input data is loaded from `feed.csv` containing feedstock specifications
- The `Shit` object maintains all feedstock and calculates derived metrics (DM rate, VS rate, gas rate, methane rate)
- Process functions mutate the feedstock properties as materials move through the plant
- Statistics are calculated at each stage using `stats()` method

## Key Files

- `model.py`: Main simulation logic with all process functions
- `feed.csv`: Input feedstock data with material properties
- `config_gui.py`: GUI application for configuring simulation parameters
- `test_model.py`: Comprehensive test suite covering all functions and integration tests
- `requirements.txt`: Python dependencies (pandas, matplotlib, reportlab, tkinter)

## New Features

### Configuration GUI

A comprehensive GUI application (`config_gui.py`) provides interactive configuration of simulation parameters:

**Features:**
- **Feedstock Configuration**: Modify intake volumes and properties for all feedstock types
- **Mix Stage Parameters**: Configure clean water rate, recirculation fluid rate and DM percentage
- **Separation Parameters**: Set sludge DM percentage and DM removal percentage
- **Load/Save Configuration**: Import/export settings as JSON files
- **Input Validation**: Ensures all parameters are valid before running simulation
- **Direct Simulation**: Run simulation with configured parameters from the GUI

**Tabs:**
- **Feedstock & Water Inputs**: Combined view with feedstock parameters table and water addition controls (clean water rate, recirculation fluid rate and DM%)
- **Separation Configuration**: Configure separation stage parameters (sludge DM%, DM removal%)

## Configuration

Process parameters are currently hardcoded as constants at the top of `model.py`:
- `SLUDGE_DM_PERCENT = 5`
- `DM_REMOVAL_PERCENT = 10` 
- `CLEAN_WATER_RATE = 1000`