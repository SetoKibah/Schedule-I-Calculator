"""
Schedule I Enterprise Suite
Main entry point for the application.
Copyright © 2025 Kibah Corps. All rights reserved.
"""

import tkinter as tk
from src.gui import ScheduleICalculatorApp

def main():
    """Launch the Schedule I Enterprise Suite application"""
    root = tk.Tk()
    
    # Try to fix ttk theme issues by setting a more compatible base theme first
    try:
        from tkinter import ttk
        available_themes = ttk.Style().theme_names()
        if 'clam' in available_themes:
            ttk.Style().theme_use('clam')  # Use clam as base theme before customization
    except Exception:
        pass  # Continue if we can't set the base theme
    
    app = ScheduleICalculatorApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()