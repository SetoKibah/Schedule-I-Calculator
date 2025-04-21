# Schedule I Profit Calculator

A comprehensive profit calculator for the game Schedule I that helps players optimize their drug mixing recipes for maximum profit.

## Features

- Calculate the market value, cost, and profit margin for any combination of base products and mixers
- Predict effects based on ingredient combinations
- Find the most profitable recipes for each base product
- Testing framework to document and analyze in-game results
- Data analyzer to suggest calculator improvements based on empirical testing

## How to Use

Run the main application to launch the GUI:

```bash
python main.py
```

For testing and data analysis:

```bash
python test_framework.py  # To document in-game observations
python data_analyzer.py   # To analyze collected data and suggest improvements
```

## Project Structure

- `main.py` - Main application entry point
- `src/` - Source code directory
  - `calculator.py` - Core calculation logic
  - `game_data.py` - Game data constants and formulas
  - `gui.py` - User interface components
- `test_framework.py` - Testing framework for documenting in-game results
- `data_analyzer.py` - Data analysis tool for improving calculator accuracy

## Notes

This calculator attempts to accurately model the in-game economy based on observations and testing. The formulas and special cases are regularly updated as more data is collected.

## License

MIT