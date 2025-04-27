"""
Schedule I Enterprise Suite
Main entry point for the application.
Copyright © 2025 Kibah Corps. All rights reserved.
"""

import tkinter as tk
import os
import threading
import time
from src.gui import ScheduleICalculatorApp
from src.dealer_data import load_dealer_data, save_dealer_data, fetch_dealers_from_urls, fix_dealer_data

# List of dealer wiki URLs
DEALER_URLS = [
    "https://schedule-1.fandom.com/wiki/Benji_Coleman",
    "https://schedule-1.fandom.com/wiki/Molly_Presley",
    "https://schedule-1.fandom.com/wiki/Brad_Crosby",
    "https://schedule-1.fandom.com/wiki/Jane_Lucero",
    "https://schedule-1.fandom.com/wiki/Wei_Long",
    "https://schedule-1.fandom.com/wiki/Leo_Rivers"
]

def fetch_dealer_data_in_background(app=None):
    """Fetch dealer data from wiki in the background
    
    Args:
        app (ScheduleICalculatorApp, optional): App instance to update status
    """
    if app:
        app.update_status("Updating dealer information in background...")
    
    # Load existing dealer data
    existing_data = load_dealer_data()
    
    # Fetch latest dealer data from wiki
    try:
        dealers = fetch_dealers_from_urls(DEALER_URLS)
        
        if dealers:
            # Get existing dealer names
            existing_names = [d["name"] for d in existing_data.get("dealers", [])]
            
            # Update existing dealers or add new ones
            for dealer in dealers:
                if dealer["name"] in existing_names:
                    # Update existing dealer
                    for i, existing_dealer in enumerate(existing_data["dealers"]):
                        if existing_dealer["name"] == dealer["name"]:
                            # Preserve transactions if not overwritten
                            if not dealer.get("transactions") and existing_dealer.get("transactions"):
                                dealer["transactions"] = existing_dealer.get("transactions", [])
                                dealer["last_transaction_date"] = existing_dealer.get("last_transaction_date", "")
                            
                            # Update with new data
                            existing_data["dealers"][i] = dealer
                            break
                else:
                    # Add new dealer
                    existing_data["dealers"].append(dealer)
            
            # Fix any missing fields
            existing_data = fix_dealer_data(existing_data)
            
            # Save updated data
            save_dealer_data(existing_data)
            
            # Update application if it was provided
            if app:
                app.load_dealer_data()  # Reload dealer data in the app
                app.update_status(f"Updated information for {len(dealers)} dealers")
                # If there's a dealer tab, refresh it
                if hasattr(app, 'refresh_dealer_list'):
                    app.refresh_dealer_list()
    except Exception as e:
        if app:
            app.update_status(f"Error updating dealer information: {str(e)}")
        print(f"Error fetching dealer data: {e}")

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
    
    # Start a background thread to fetch dealer data
    # Wait a moment for the app to initialize before fetching
    def delayed_fetch():
        time.sleep(2)  # Give the app time to initialize
        fetch_dealer_data_in_background(app)
    
    # Start background update thread
    fetch_thread = threading.Thread(target=delayed_fetch)
    fetch_thread.daemon = True  # Thread will exit when main thread exits
    fetch_thread.start()
    
    root.mainloop()

if __name__ == "__main__":
    main()