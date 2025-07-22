# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a biogas plant simulation written in Python that models the anaerobic digestion process. The simulation tracks feedstock through multiple stages: feeding, mixing, digestion, pasteurization, and separation.

## Development Commands

### Running the Simulation
```bash
python model.py
```

This will run the simulation and generate both console output and a PDF report (`biogas_simulation_report.pdf`).

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
- `test_model.py`: Comprehensive test suite covering all functions and integration tests
- `requirements.txt`: Python dependencies (pandas, matplotlib, reportlab)

## New Features

### PDF Report Generation

The simulation now includes automatic PDF report generation:

- **`generate_pdf_report()`**: Creates a formatted PDF with all simulation data
- **`run_simulation_with_pdf()`**: Runs the complete simulation and generates a PDF report
- Reports include formatted tables for each process stage, DM percentages, methane yield, and separation results
- PDF files are generated with timestamp and professional formatting

## Configuration

Process parameters are currently hardcoded as constants at the top of `model.py`:
- `SLUDGE_DM_PERCENT = 5`
- `DM_REMOVAL_PERCENT = 10` 
- `CLEAN_WATER_RATE = 1000`