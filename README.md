# Schedule I Enterprise Suite

A comprehensive business management application for the game Schedule I that helps players optimize their drug mixing recipes for maximum profit, manage customer data, and track business operations.

Copyright © 2025 Kibah Corps. All rights reserved.

## Features

- **Profit Calculator**: Calculate the market value, cost, and profit margin for any combination of base products and mixers
- **Effects Preview**: Instantly see how different mixers will affect your product
- **Recipe Management**: Save and compare custom recipes to find your most profitable combinations
- **Top Recipes Analysis**: Automatically find the most profitable recipes for each base product
- **Customer Database**: Track customer preferences, locations, relations, and purchase history
- **Game Data Repository**: Browse comprehensive reference data on all in-game products and effects
- **Data Analysis Tools**: Analyze test results and improve business strategies
- **Improved Loading Experience**: Granular progress updates during startup for better user experience

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

For manual data fetching:

```bash
python fetch_dealers_improved.py  # Fetch dealer data from the Schedule I wiki
```

## Project Structure

- `main.py` - Main application entry point
- `src/` - Source code directory
  - `calculator.py` - Core calculation logic for product profitability
  - `game_data.py` - Game data constants, effects, and formulas
  - `gui.py` - User interface components and application logic
  - `customer_data.py` - Customer data management utilities
  - `dealer_data.py` - Dealer data management utilities
- `test_framework.py` - Testing framework for documenting in-game results
- `data_analyzer.py` - Data analysis tool for improving calculator accuracy
- `fetch_dealers_improved.py` - Script for fetching dealer data from the wiki
- `customer_data.json` - Local database file for customer information (not tracked in git)
- `dealer_data.json` - Local database file for dealer information (not tracked in git)
- `game_data.json` - Local database file for custom game data (not tracked in git)

## Development

This application is regularly updated with new features and improved accuracy as more in-game data is collected. The software models the in-game economy based on extensive testing and analysis.

### Recent Updates

- **Enhanced Data Loading**: Implemented granular progress updates during application startup
- **Reliable Dealer Data Fetching**: Improved web scraping of dealer information from the Schedule I wiki
- **Preserved Custom Settings**: Data updates now preserve custom settings and assignments

### Contributing

Contributions are welcome! If you'd like to contribute, please:

1. Fork the repository
2. Create a feature branch
3. Submit a pull request with a clear description of your changes

## Notes

This business management suite attempts to accurately model the in-game economy based on observations and testing. The formulas and special cases are regularly updated as more data is collected.

## License

MIT License

## Acknowledgments

- Schedule I game developers for creating an engaging business simulation
- Community members who have contributed test data and feedback