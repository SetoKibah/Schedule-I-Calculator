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
import tkinter.ttk as ttk

# List of dealer wiki URLs
DEALER_URLS = [
    "https://schedule-1.fandom.com/wiki/Benji_Coleman",
    "https://schedule-1.fandom.com/wiki/Molly_Presley",
    "https://schedule-1.fandom.com/wiki/Brad_Crosby",
    "https://schedule-1.fandom.com/wiki/Jane_Lucero",
    "https://schedule-1.fandom.com/wiki/Wei_Long",
    "https://schedule-1.fandom.com/wiki/Leo_Rivers"
]

def fetch_dealer_data(progress_callback=None):
    """Fetch dealer data from wiki while preserving customer assignments
    
    Args:
        progress_callback (function, optional): Callback function to update progress
    
    Returns:
        dict: Updated dealer data with preserved customer assignments
    """
    from src.dealer_data import update_dealers_preserve_assignments
    
    try:
        if progress_callback:
            progress_callback("Starting dealer data update...", 0)
        
        # Use our new function that preserves customer assignments
        updated_data = update_dealers_preserve_assignments()
        
        if progress_callback:
            progress_callback(f"Completed updating dealer data. Customer assignments preserved.", 100)
        
        return updated_data
    
    except Exception as e:
        if progress_callback:
            progress_callback(f"Error: {str(e)}", 100)
        print(f"Error updating dealer data: {e}")
        
        # If there's an error, just load the existing data
        from src.dealer_data import load_dealer_data
        return load_dealer_data()

def fetch_all_data(progress_callback=None):
    """Fetch all application data (dealers, customers, game data) while preserving assignments
    
    Args:
        progress_callback (function, optional): Callback function to update progress
    
    Returns:
        tuple: (dealer_data, customer_data, game_data) - All updated data
    """
    try:
        # Set up progress tracking
        total_steps = 3  # dealers, customers, game data
        current_step = 0
        
        if progress_callback:
            progress_callback("Starting data update...", 0)
        
        # Step 1: Update dealer data while preserving customer assignments
        current_step += 1
        step_base = (current_step-1) * 100 / total_steps
        step_range = 100 / total_steps
        
        # Create a nested progress callback for more granular updates
        def dealer_progress(message, percentage):
            if progress_callback:
                # Convert the percentage within this step to overall percentage
                overall_percentage = step_base + (percentage * step_range / 100)
                progress_callback(message, overall_percentage)
        
        if progress_callback:
            dealer_progress("Updating dealer data...", 0)
        
        from src.dealer_data import update_dealers_preserve_assignments
        dealer_data = update_dealers_preserve_assignments(progress_callback=dealer_progress)
        
        # Step 2: Update customer data while preserving dealer assignments
        current_step += 1
        step_base = (current_step-1) * 100 / total_steps
        step_range = 100 / total_steps
        
        # Create a nested progress callback for customer data
        def customer_progress(message, percentage):
            if progress_callback:
                overall_percentage = step_base + (percentage * step_range / 100)
                progress_callback(message, overall_percentage)
        
        if progress_callback:
            customer_progress("Updating customer data...", 0)
        
        from src.customer_data import update_customers_preserve_assignments
        customer_data = update_customers_preserve_assignments(progress_callback=customer_progress)
        
        # Step 3: Update game data while preserving custom settings
        current_step += 1
        step_base = (current_step-1) * 100 / total_steps
        step_range = 100 / total_steps
        
        # Create a nested progress callback for game data
        def game_progress(message, percentage):
            if progress_callback:
                overall_percentage = step_base + (percentage * step_range / 100)
                progress_callback(message, overall_percentage)
        
        if progress_callback:
            game_progress("Updating game data...", 0)
        
        from src.game_data import update_game_data_preserve_custom_settings
        game_data = update_game_data_preserve_custom_settings(progress_callback=game_progress)
        
        if progress_callback:
            progress_callback("All data updated successfully!", 100)
            
        return (dealer_data, customer_data, game_data)
        
    except Exception as e:
        if progress_callback:
            progress_callback(f"Error updating data: {e}", 100)
        print(f"Error updating application data: {e}")
        
        # Return None values in case of failure
        return (None, None, None)

def show_startup_window():
    """Show a startup window while fetching all application data"""
    startup_window = tk.Tk()
    startup_window.title("Schedule I Enterprise Suite - Starting Up")
    startup_window.geometry("400x150")
    startup_window.resizable(False, False)
    
    # Set window to appear in center of screen
    screen_width = startup_window.winfo_screenwidth()
    screen_height = startup_window.winfo_screenheight()
    x = (screen_width - 400) // 2
    y = (screen_height - 150) // 2
    startup_window.geometry(f"400x150+{x}+{y}")
    
    # Configure a dark green theme similar to main app
    dark_green = "#1E3F20"
    mid_green = "#345830"
    text_color = "#FFFFFF"
    
    startup_window.configure(bg=dark_green)
    
    # Title
    title_label = tk.Label(
        startup_window,
        text="Schedule I Enterprise Suite",
        font=("Arial", 14, "bold"),
        fg=text_color,
        bg=dark_green
    )
    title_label.pack(pady=(20, 5))
    
    # Status message
    status_var = tk.StringVar(value="Initializing...")
    status_label = tk.Label(
        startup_window,
        textvariable=status_var,
        font=("Arial", 10),
        fg=text_color,
        bg=dark_green
    )
    status_label.pack(pady=5)
    
    # Progress bar
    progress_var = tk.DoubleVar(value=0)
    progress_bar = ttk.Progressbar(
        startup_window, 
        variable=progress_var,
        maximum=100,
        length=350
    )
    progress_bar.pack(pady=10)
    
    # Create a function to update progress
    def update_progress(message, percentage):
        status_var.set(message)
        progress_var.set(percentage)
        startup_window.update()
    
    # Function to start data fetching and launch main app
    def start_fetching():
        # Fetch all application data with progress updates
        dealer_data, customer_data, game_data = fetch_all_data(update_progress)
        
        # Close startup window
        startup_window.destroy()
        
        # Launch main application with the updated data
        launch_main_app(dealer_data, customer_data, game_data)
    
    # Schedule the fetching to start soon
    startup_window.after(100, start_fetching)
    
    # Start the window's main loop
    startup_window.mainloop()

def launch_main_app(dealer_data=None, customer_data=None, game_data=None):
    """Launch the main application with pre-loaded data"""
    root = tk.Tk()
    
    # Try to fix ttk theme issues by setting a more compatible base theme first
    try:
        available_themes = ttk.Style().theme_names()
        if 'clam' in available_themes:
            ttk.Style().theme_use('clam')  # Use clam as base theme before customization
    except Exception:
        pass  # Continue if we can't set the base theme
    
    app = ScheduleICalculatorApp(root)
    
    # Load all pre-fetched data into the app
    if dealer_data and hasattr(app, 'dealer_data'):
        app.dealer_data = dealer_data
        app.update_status(f"Loaded data for {len(dealer_data.get('dealers', []))} dealers")
    
    if customer_data and hasattr(app, 'customer_data'):
        app.customer_data = customer_data
        app.update_status(f"Loaded data for {len(customer_data.get('customers', []))} customers")
    
    if game_data and hasattr(app, 'game_data'):
        app.game_data = game_data
        app.update_status(f"Loaded game data with {len(game_data.get('EFFECTS', {}))} effects")
    
    # Update status to indicate all data is loaded
    if dealer_data and customer_data and game_data:
        app.update_status(f"All application data updated and loaded successfully")
    
    root.mainloop()

def main():
    """Launch the Schedule I Enterprise Suite application"""
    # Show startup window and begin fetch process
    show_startup_window()

if __name__ == "__main__":
    main()