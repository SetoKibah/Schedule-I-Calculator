"""
Schedule I Enterprise Suite
A user interface for tracking and comparing drug mixes in Schedule I.
Copyright © 2025 Kibah Corps. All rights reserved.
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import json
import os
import requests
from bs4 import BeautifulSoup
import re
import datetime
from src.calculator import calculate_profit, compare_mixes, get_effects_from_mixers
from src.game_data import BASE_MARKET_VALUES, MARIJUANA_STRAINS, MIXERS, EFFECTS, RECIPES


class ScheduleICalculatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Schedule I Enterprise Suite")
        self.root.geometry("900x700")
        self.root.resizable(True, True)
        self.root.minsize(800, 600)  # Set minimum window size
        
        # Configure root window to expand widgets properly
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=0)  # Status bar row
        
        # Data file paths
        self.customer_data_file = "customer_data.json"
        
        # Load customer data
        self.customer_data = self.load_customer_data()
        
        # Setup custom theme with dark green to light green colors
        self.setup_theme()
        
        # Create a frame for the main content (tabs)
        main_frame = ttk.Frame(root)
        main_frame.grid(row=0, column=0, sticky="nsew")
        
        # Create tabs
        self.tab_control = ttk.Notebook(main_frame)
        
        self.calculator_tab = ttk.Frame(self.tab_control)
        self.recipe_tab = ttk.Frame(self.tab_control)
        self.compare_tab = ttk.Frame(self.tab_control)
        self.top_recipes_tab = ttk.Frame(self.tab_control)
        self.data_tab = ttk.Frame(self.tab_control)
        self.customers_tab = ttk.Frame(self.tab_control)  # New customers tab
        
        self.tab_control.add(self.calculator_tab, text="Calculator")
        self.tab_control.add(self.recipe_tab, text="Recipes")
        self.tab_control.add(self.compare_tab, text="Compare")
        self.tab_control.add(self.top_recipes_tab, text="Top Recipes")
        self.tab_control.add(self.data_tab, text="Game Data")
        self.tab_control.add(self.customers_tab, text="Customers")  # Add customers tab
        
        self.tab_control.pack(expand=1, fill="both")
        
        # Create status bar at the bottom of the window
        self.status_var = tk.StringVar(value="Ready - Select a tab to get started")
        self.status_bar = ttk.Label(
            root, 
            textvariable=self.status_var,
            relief=tk.SUNKEN,
            anchor=tk.W,
            padding=(10, 2),
            background=self.mid_green,
            foreground=self.text_color
        )
        self.status_bar.grid(row=1, column=0, sticky="ew")
        
        # Initialize tabs
        self.setup_calculator_tab()
        self.setup_recipe_tab()
        self.setup_compare_tab()
        self.setup_top_recipes_tab()
        self.setup_data_tab()
        self.setup_customers_tab()  # Initialize the new customers tab
        
        # Bind tab change event to update status bar
        self.tab_control.bind("<<NotebookTabChanged>>", self.update_status_on_tab_change)
        
        # Store user-created mixes
        self.user_mixes = []
        
        # Custom sort state to track sorting order
        self.customer_sort_column = None
        self.customer_sort_reverse = False
    
    def setup_theme(self):
        """Setup custom dark green to light green theme"""
        # Define colors
        self.dark_green = "#1E3F20"    # Very dark green for backgrounds
        self.mid_green = "#345830"     # Mid-tone green for highlights
        self.light_green = "#4F7942"   # Forest green for buttons
        self.accent_green = "#88B378"  # Light sage green for accents
        self.text_color = "#FFFFFF"    # Pure white for better visibility
        self.highlight_color = "#98FB98" # Pale green for highlights
        self.header_bg = "#2D4F2D"     # Slightly lighter than dark_green for headers
        
        # Font configuration for improved visual hierarchy
        self.title_font = ("Arial", 14, "bold")
        self.subtitle_font = ("Arial", 12, "bold")
        self.body_font = ("Arial", 10)
        self.small_font = ("Arial", 9)
        
        # Configure ttk style
        self.style = ttk.Style()
        
        # Configure the theme using ttk elements
        
        # Main elements
        self.style.configure("TFrame", background=self.dark_green)
        self.style.configure("TLabel", background=self.dark_green, foreground=self.text_color, font=self.body_font)
        
        # Create title and subtitle styles
        self.style.configure("Title.TLabel", font=self.title_font, background=self.dark_green, foreground=self.text_color)
        self.style.configure("Subtitle.TLabel", font=self.subtitle_font, background=self.dark_green, foreground=self.text_color)
        
        # Button - with explicit foreground and background
        self.style.configure("TButton", 
                            background=self.light_green, 
                            foreground=self.text_color,
                            font=self.body_font,
                            relief=tk.RAISED)
        self.style.map("TButton", 
                      background=[('active', self.accent_green), ('pressed', self.mid_green)],
                      foreground=[('active', self.text_color), ('pressed', self.text_color)])
        self.style.configure("TNotebook", background=self.dark_green, borderwidth=0)
        self.style.configure("TNotebook.Tab", 
                            background=self.mid_green, 
                            foreground=self.text_color,
                            font=self.body_font,
                            padding=[10, 5])
        self.style.map("TNotebook.Tab",
                      background=[('selected', self.light_green), ('active', self.accent_green)],
                      foreground=[('selected', "#FFFFFF"), ('active', "#FFFFFF")])
        
        # Combobox - ensuring text is visible
        self.style.configure("TCombobox", 
                            fieldbackground=self.mid_green, 
                            background=self.light_green,
                            foreground=self.text_color,
                            font=self.body_font,
                            selectbackground=self.accent_green,
                            selectforeground=self.text_color,
                            arrowcolor=self.text_color)
        self.style.map("TCombobox",
                      fieldbackground=[('readonly', self.mid_green)],
                      selectbackground=[('readonly', self.accent_green)],
                      selectforeground=[('readonly', self.text_color)])
        
        # Force combobox dropdown to be readable
        self.root.option_add('*TCombobox*Listbox.background', self.mid_green)
        self.root.option_add('*TCombobox*Listbox.foreground', self.text_color)
        self.root.option_add('*TCombobox*Listbox.selectBackground', self.accent_green)
        self.root.option_add('*TCombobox*Listbox.selectForeground', self.text_color)
        self.root.option_add('*TCombobox*Listbox.font', self.body_font)
        
        # Entry
        self.style.configure("TEntry", 
                            fieldbackground=self.mid_green,
                            font=self.body_font,
                            foreground=self.text_color)
        
        # Checkbutton
        self.style.configure("TCheckbutton", 
                            background=self.dark_green,
                            font=self.body_font,
                            foreground=self.text_color)
        self.style.map("TCheckbutton",
                      background=[('active', self.dark_green)],
                      foreground=[('active', self.highlight_color)])
        
        # Treeview (for tables)
        self.style.configure("Treeview", 
                            background=self.mid_green,
                            fieldbackground=self.mid_green,
                            font=self.body_font,
                            foreground=self.text_color)
        self.style.configure("Treeview.Heading", 
                            background=self.header_bg,
                            font=("Arial", 10, "bold"),
                            relief="raised",
                            borderwidth=1,
                            foreground=self.text_color)
        self.style.map("Treeview",
                      background=[('selected', self.light_green)],
                      foreground=[('selected', self.text_color)])
        
        # LabelFrame
        self.style.configure("TLabelframe", background=self.dark_green)
        self.style.configure("TLabelframe.Label", 
                             background=self.dark_green, 
                             foreground=self.text_color, 
                             font=self.subtitle_font)
        
        # Scrollbar
        self.style.configure("Vertical.TScrollbar", 
                            background=self.mid_green,
                            arrowcolor=self.text_color,
                            troughcolor=self.dark_green)
        
        # Configure root window background
        self.root.configure(background=self.dark_green)
        
        # Configure text widget styles (these aren't ttk widgets)
        text_opts = {
            "background": self.mid_green,
            "foreground": self.text_color,
            "insertbackground": self.text_color,  # cursor color
            "selectbackground": self.light_green,
            "selectforeground": self.text_color,
            "borderwidth": 1,
            "font": self.body_font,
            "relief": tk.SUNKEN
        }
        
        # Save these as a reference for later
        self.text_widget_options = text_opts
        
    def _configure_scrolledtext(self, text_widget):
        """Apply theme to a scrolledtext widget"""
        text_widget.configure(
            background=self.mid_green,
            foreground=self.text_color,
            insertbackground=self.text_color,
            selectbackground=self.light_green,
            selectforeground=self.text_color
        )
        
        # Configure the scrollbar
        for child in text_widget.winfo_children():
            if isinstance(child, ttk.Scrollbar):
                child.configure(style="Vertical.TScrollbar")
                
    def setup_calculator_tab(self):
        """Setup the calculator tab for single mix analysis"""
        frame = ttk.Frame(self.calculator_tab, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Configure grid weights for responsive resizing
        frame.columnconfigure(0, weight=0)
        frame.columnconfigure(1, weight=1)
        for i in range(8):
            frame.rowconfigure(i, weight=0)
        frame.rowconfigure(6, weight=1)  # Make results text expand
        
        # Base product selection
        ttk.Label(frame, text="Base Product:").grid(row=0, column=0, sticky=tk.W, pady=5)
        
        # Combine regular products and marijuana strains
        self.base_products = list(BASE_MARKET_VALUES.keys()) + list(MARIJUANA_STRAINS.keys())
        self.base_var = tk.StringVar(value=self.base_products[0])
        
        base_dropdown = ttk.Combobox(frame, textvariable=self.base_var, values=self.base_products)
        base_dropdown.grid(row=0, column=1, sticky=tk.W, pady=5)
        base_dropdown.bind("<<ComboboxSelected>>", self.update_effects_preview)
        
        # Mixers selection - now the primary input
        ttk.Label(frame, text="Mixers (select in application order):").grid(row=1, column=0, sticky=tk.NW, pady=5)
        
        # Frame for mixers and effects preview side by side
        input_frame = ttk.Frame(frame)
        input_frame.grid(row=1, column=1, sticky=tk.W+tk.E, pady=5)  # Changed sticky to expand horizontally
        
        # Configure input frame for responsive sizing
        input_frame.columnconfigure(0, weight=1)
        input_frame.columnconfigure(1, weight=1)
        
        # Mixers selection on the left
        self.mixers_frame = ttk.Frame(input_frame)
        self.mixers_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))  # Added expand=True
        
        self.mixer_vars = {}
        self.mixer_order = []  # To track mixer application order
        
        # Create a canvas for scrollable mixers
        mixers_canvas = tk.Canvas(self.mixers_frame, width=250, height=300, 
                                 bg=self.mid_green, highlightbackground=self.dark_green)
        mixers_scrollbar = ttk.Scrollbar(self.mixers_frame, orient="vertical", command=mixers_canvas.yview)
        mixers_canvas.configure(yscrollcommand=mixers_scrollbar.set)
        
        mixers_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        mixers_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        mixers_inner_frame = ttk.Frame(mixers_canvas)
        mixers_canvas.create_window((0, 0), window=mixers_inner_frame, anchor=tk.NW)
        
        # Add checkboxes for all mixers
        row = 0
        for mixer in sorted(MIXERS.keys()):
            self.mixer_vars[mixer] = tk.BooleanVar(value=False)
            cb = ttk.Checkbutton(
                mixers_inner_frame, 
                text=f"{mixer} (${MIXERS[mixer]['cost']})", 
                variable=self.mixer_vars[mixer],
                command=lambda m=mixer: self.on_mixer_toggled(m)
            )
            cb.grid(row=row, column=0, sticky=tk.W, padx=5)
            row += 1
        
        mixers_inner_frame.update_idletasks()
        mixers_canvas.config(scrollregion=mixers_canvas.bbox("all"))
        
        # Effects preview on the right
        self.effects_preview_frame = ttk.LabelFrame(input_frame, text="Effects Preview")
        self.effects_preview_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        self.effects_preview = scrolledtext.ScrolledText(self.effects_preview_frame, width=30, height=15, wrap=tk.WORD)
        self.effects_preview.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self._configure_scrolledtext(self.effects_preview)
        
        # Mix name
        ttk.Label(frame, text="Mix Name:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.mix_name_var = tk.StringVar(value="My Custom Mix")
        ttk.Entry(frame, textvariable=self.mix_name_var).grid(row=2, column=1, sticky=tk.W+tk.E, pady=5)
        
        # Mix order frame - show the order of mixers
        ttk.Label(frame, text="Mixing Order:").grid(row=3, column=0, sticky=tk.NW, pady=5)
        
        order_frame = ttk.Frame(frame)
        order_frame.grid(row=3, column=1, sticky=tk.W+tk.E, pady=5)  # Changed sticky to expand horizontally
        
        # Make order_frame use all available width
        order_frame.columnconfigure(0, weight=1)
        
        # Reduced height from 5 to 3 to make the mixing order display more compact
        self.order_display = scrolledtext.ScrolledText(order_frame, width=50, height=3, wrap=tk.WORD)
        self.order_display.pack(fill=tk.BOTH, expand=True)
        self._configure_scrolledtext(self.order_display)
        
        # Button to manually adjust the order - align to right
        adjust_order_btn = ttk.Button(order_frame, text="Edit Mixing Order", command=self.edit_mixing_order)
        adjust_order_btn.pack(anchor=tk.E, pady=(5, 0))
        
        # Calculate button
        calculate_btn = ttk.Button(frame, text="Calculate Profit", command=self.calculate_single_mix)
        calculate_btn.grid(row=4, column=0, columnspan=2, pady=10)
        
        # Results section
        ttk.Label(frame, text="Results:", font=("Arial", 12, "bold")).grid(row=5, column=0, sticky=tk.W, pady=5)
        
        self.results_text = scrolledtext.ScrolledText(frame, width=70, height=10, wrap=tk.WORD)
        self.results_text.grid(row=6, column=0, columnspan=2, pady=5)
        self._configure_scrolledtext(self.results_text)
        
        # Save mix button
        save_btn = ttk.Button(frame, text="Save Mix", command=self.save_mix)
        save_btn.grid(row=7, column=0, columnspan=2, pady=10)
        
        # Initialize the effects preview
        self.update_effects_preview()
    
    def on_mixer_toggled(self, mixer):
        """Handle mixer checkbox toggled"""
        is_checked = self.mixer_vars[mixer].get()
        
        if is_checked:
            # Add to order if not already there
            if mixer not in self.mixer_order:
                self.mixer_order.append(mixer)
        else:
            # Remove from order
            if mixer in self.mixer_order:
                self.mixer_order.remove(mixer)
        
        # Update displays
        self.update_order_display()
        self.update_effects_preview()
    
    def update_order_display(self):
        """Update the display of the mixer order"""
        self.order_display.delete(1.0, tk.END)
        
        if not self.mixer_order:
            self.order_display.insert(tk.END, "No mixers added yet.")
            return
        
        for i, mixer in enumerate(self.mixer_order, 1):
            self.order_display.insert(tk.END, f"{i}. {mixer}\n")
    
    def edit_mixing_order(self):
        """Open a dialog to manually edit the mixing order"""
        if not self.mixer_order:
            messagebox.showinfo("No Mixers", "Please add mixers first.")
            self.update_status("No mixers available to reorder")
            return
        
        # Create a popup dialog
        dialog = tk.Toplevel(self.root)
        dialog.title("Edit Mixing Order")
        dialog.geometry("400x400")
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.configure(background=self.dark_green)
        
        # Add styled title
        ttk.Label(dialog, text="Drag mixers to reorder:", style="Subtitle.TLabel").pack(pady=10)
        
        # Frame for listbox and controls
        listbox_frame = ttk.Frame(dialog)
        listbox_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Create a custom styled listbox for drag and drop reordering
        order_list = tk.Listbox(
            listbox_frame, 
            height=15, 
            width=40,
            selectbackground=self.light_green,
            selectforeground=self.text_color,
            background=self.mid_green,
            foreground=self.text_color,
            font=self.body_font,
            activestyle="none",
            highlightbackground=self.dark_green,
            highlightcolor=self.accent_green,
            bd=1
        )
        order_list.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        
        # Add scrollbar for listbox
        scrollbar = ttk.Scrollbar(listbox_frame, orient=tk.VERTICAL, command=order_list.yview)
        order_list.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Fill with current order
        for mixer in self.mixer_order:
            order_list.insert(tk.END, mixer)
        
        # Store the drag start index
        drag_data = {"start_index": None, "current_selection": None}
        
        # Add drag and drop functionality
        def on_drag_start(event):
            # Get the index of the selected item
            widget = event.widget
            index = widget.nearest(event.y)
            drag_data["start_index"] = index
            drag_data["current_selection"] = widget.get(index)
            
            # Visual feedback - add a tag or change color to show selected item
            widget.selection_clear(0, tk.END)
            widget.selection_set(index)
        
        def on_drag_motion(event):
            # Get the index of the item under the cursor
            widget = event.widget
            index = widget.nearest(event.y)
            
            # Do nothing if we're on the same item or no item was selected
            if drag_data["start_index"] is None or index == drag_data["start_index"]:
                return
            
            # Move the item
            selected_item = drag_data["current_selection"]
            start_index = drag_data["start_index"]
            
            # Remove from old position and insert at new position
            widget.delete(start_index)
            widget.insert(index, selected_item)
            
            # Update the start_index for next movement
            drag_data["start_index"] = index
            
            # Visual feedback - keep the moved item selected
            widget.selection_clear(0, tk.END)
            widget.selection_set(index)
        
        def on_drag_release(event):
            # Reset drag data
            drag_data["start_index"] = None
            drag_data["current_selection"] = None
        
        # Bind the events
        order_list.bind('<Button-1>', on_drag_start)
        order_list.bind('<B1-Motion>', on_drag_motion)
        order_list.bind('<ButtonRelease-1>', on_drag_release)
        
        # Movement buttons for finer control
        button_frame = ttk.Frame(dialog)
        button_frame.pack(fill=tk.X, padx=10, pady=5)
        
        def move_item_up():
            selected = order_list.curselection()
            if not selected or selected[0] == 0:
                return
            
            index = selected[0]
            item = order_list.get(index)
            order_list.delete(index)
            order_list.insert(index-1, item)
            order_list.selection_clear(0, tk.END)
            order_list.selection_set(index-1)
            order_list.see(index-1)
        
        def move_item_down():
            selected = order_list.curselection()
            if not selected or selected[0] == order_list.size()-1:
                return
            
            index = selected[0]
            item = order_list.get(index)
            order_list.delete(index)
            order_list.insert(index+1, item)
            order_list.selection_clear(0, tk.END)
            order_list.selection_set(index+1)
            order_list.see(index+1)
        
        # Add move up/down buttons for precise movement
        move_up_btn = ttk.Button(button_frame, text="Move Up", command=move_item_up)
        move_up_btn.pack(side=tk.LEFT, padx=5)
        
        move_down_btn = ttk.Button(button_frame, text="Move Down", command=move_item_down)
        move_down_btn.pack(side=tk.LEFT, padx=5)
        
        # Buttons
        action_frame = ttk.Frame(dialog)
        action_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(action_frame, text="OK", command=lambda: self._apply_new_order(order_list, dialog)).pack(side=tk.RIGHT, padx=5)
        ttk.Button(action_frame, text="Cancel", command=dialog.destroy).pack(side=tk.RIGHT, padx=5)
    
    def _apply_new_order(self, listbox, dialog):
        """Apply the new mixer order from the dialog"""
        # Get all items from listbox
        new_order = [listbox.get(i) for i in range(listbox.size())]
        
        # Update mixer order
        self.mixer_order = new_order
        
        # Update displays
        self.update_order_display()
        self.update_effects_preview()
        
        # Update status
        self.update_status(f"Mixing order updated - {len(new_order)} mixers in sequence")
        
        # Close dialog
        dialog.destroy()
    
    def update_effects_preview(self, event=None):
        """Update the effects preview based on base product and mixers"""
        base_product = self.base_var.get()
        
        # Get list of mixers in application order
        mixers = self.mixer_order.copy()
        
        # Calculate effects
        effects = get_effects_from_mixers(base_product, mixers)
        
        # Update preview
        self.effects_preview.delete(1.0, tk.END)
        
        if not effects:
            self.effects_preview.insert(tk.END, "No effects applied.")
            return
        
        self.effects_preview.insert(tk.END, f"Effects ({len(effects)}/8):\n\n")
        
        # Calculate total multiplier
        total_multiplier = 0
        
        for effect in effects:
            multiplier = EFFECTS[effect]["multiplier"]
            total_multiplier += multiplier
            self.effects_preview.insert(tk.END, f"• {effect} (+{multiplier})\n")
        
        self.effects_preview.insert(tk.END, f"\nTotal Multiplier: +{total_multiplier:.2f}")
    
    def setup_recipe_tab(self):
        """Setup the recipe tab for pre-defined recipes"""
        frame = ttk.Frame(self.recipe_tab, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Configure grid weights for responsive resizing
        frame.columnconfigure(0, weight=0)
        frame.columnconfigure(1, weight=1)
        frame.rowconfigure(2, weight=1)  # Make recipe details expand
        
        # Recipe selection
        ttk.Label(frame, text="Select Recipe:").grid(row=0, column=0, sticky=tk.W, pady=5)
        
        self.recipe_var = tk.StringVar(value=list(RECIPES.keys())[0])
        recipe_dropdown = ttk.Combobox(frame, textvariable=self.recipe_var, values=list(RECIPES.keys()))
        recipe_dropdown.grid(row=0, column=1, sticky=tk.W+tk.E, pady=5)
        recipe_dropdown.bind("<<ComboboxSelected>>", self.update_recipe_details)
        
        # Recipe details
        ttk.Label(frame, text="Recipe Details:", font=("Arial", 12, "bold")).grid(row=1, column=0, sticky=tk.W, pady=5)
        
        self.recipe_details = scrolledtext.ScrolledText(frame, width=70, height=20, wrap=tk.WORD)
        self.recipe_details.grid(row=2, column=0, columnspan=2, sticky=tk.NSEW, pady=5)
        self._configure_scrolledtext(self.recipe_details)
        
        # Calculate recipe button
        calculate_btn = ttk.Button(frame, text="Calculate Recipe Profit", command=self.calculate_recipe)
        calculate_btn.grid(row=3, column=0, columnspan=2, pady=10)
        
        # Initialize with first recipe
        self.update_recipe_details()
    
    def setup_compare_tab(self):
        """Setup the compare tab for comparing multiple mixes"""
        frame = ttk.Frame(self.compare_tab, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Configure grid weights for responsive resizing
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(1, weight=1)  # Make results table expand
        frame.rowconfigure(3, weight=1)  # Make details expand
        
        # Compare button
        compare_btn = ttk.Button(frame, text="Compare All Saved & Predefined Mixes", command=self.compare_all_mixes)
        compare_btn.grid(row=0, column=0, sticky="nw", pady=10)
        
        # Results table - Using our new FixedHeader widget for sticky headers
        columns = ("Name", "Base", "Market Value", "Cost", "Profit", "Profit %", "Mixes")
        self.compare_tree = FixedHeader(frame, columns=columns, height=15)
        self.compare_tree.grid(row=1, column=0, sticky="nsew", pady=5)
        
        # Configure column widths
        for col in columns:
            width = 150 if col in ("Name", "Base") else 100
            self.compare_tree.column(col, width=width)
            # Set column headings
            if col == "Profit %":
                self.compare_tree.heading(col, text="Profit %")
            else:
                self.compare_tree.heading(col, text=col)
        
        # Details for selected mix
        ttk.Label(frame, text="Selected Mix Details:", style="Subtitle.TLabel").grid(row=2, column=0, sticky=tk.W, pady=5)
        
        self.compare_details = scrolledtext.ScrolledText(frame, width=70, height=10, wrap=tk.WORD)
        self.compare_details.grid(row=3, column=0, sticky=tk.NSEW, pady=5)
        self._configure_scrolledtext(self.compare_details)
        
        # Bind selection event
        self.compare_tree.bind("<<TreeviewSelect>>", self.show_selected_mix_details)
        
        # Make the frame resizable
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(1, weight=1)
    
    def setup_top_recipes_tab(self):
        """Setup the top recipes tab for viewing top profit recipes for each product"""
        frame = ttk.Frame(self.top_recipes_tab, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Configure grid weights for responsive resizing
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(1, weight=0)
        frame.rowconfigure(2, weight=0)
        frame.rowconfigure(3, weight=1)  # Make results notebook expand
        
        # Controls
        control_frame = ttk.Frame(frame)
        control_frame.pack(fill=tk.X, pady=10)
        
        # Product selection
        ttk.Label(control_frame, text="Select Product:").pack(side=tk.LEFT, padx=5)
        
        all_products = ["All Products"] + list(BASE_MARKET_VALUES.keys()) + list(MARIJUANA_STRAINS.keys())
        self.top_recipe_product_var = tk.StringVar(value=all_products[0])
        
        product_dropdown = ttk.Combobox(control_frame, textvariable=self.top_recipe_product_var, values=all_products, width=25)
        product_dropdown.pack(side=tk.LEFT, padx=5)
        product_dropdown.bind("<<ComboboxSelected>>", self.update_top_recipes_display)
        
        # Number of recipes
        ttk.Label(control_frame, text="Number of top recipes:").pack(side=tk.LEFT, padx=(20, 5))
        
        self.top_n_var = tk.IntVar(value=5)
        top_n_spinbox = ttk.Spinbox(control_frame, from_=1, to=10, textvariable=self.top_n_var, width=5)
        top_n_spinbox.pack(side=tk.LEFT, padx=5)
        
        # Max Mixers control - NEW!
        ttk.Label(control_frame, text="Max mixers:").pack(side=tk.LEFT, padx=(20, 5))
        
        self.max_mixers_var = tk.IntVar(value=8)  # Default to 8 (maximum)
        max_mixers_values = list(range(1, 9))  # 1-8 mixers
        max_mixers_spinbox = ttk.Spinbox(
            control_frame, 
            from_=1, 
            to=8, 
            textvariable=self.max_mixers_var, 
            width=5,
            values=max_mixers_values
        )
        max_mixers_spinbox.pack(side=tk.LEFT, padx=5)
        
        # Equipment info tooltip
        equipment_tooltip = ttk.Label(control_frame, text="ℹ️", cursor="hand2", font=("Arial", 12))
        equipment_tooltip.pack(side=tk.LEFT)
        equipment_tooltip.bind("<Enter>", lambda e: self.show_equipment_tooltip(e))
        equipment_tooltip.bind("<Leave>", lambda e: self.hide_equipment_tooltip(e))
        
        # Calculate button
        calculate_btn = ttk.Button(control_frame, text="Calculate Top Recipes", command=self.calculate_top_recipes)
        calculate_btn.pack(side=tk.RIGHT, padx=5)
        
        # Progress indicator
        self.progress_var = tk.StringVar(value="")
        progress_label = ttk.Label(frame, textvariable=self.progress_var)
        progress_label.pack(anchor=tk.W, pady=5)
        
        # Results notebook - one tab per product
        self.top_recipes_notebook = ttk.Notebook(frame)
        self.top_recipes_notebook.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # We'll populate tabs dynamically when the user clicks "Calculate"
        
        # Description of the feature
        help_frame = ttk.LabelFrame(frame, text="About This Feature")
        help_frame.pack(fill=tk.X, pady=10)
        
        help_text = "This feature analyzes thousands of possible mixer combinations to find the highest profit margin recipes for each product type.\n\n"
        help_text += "The algorithm uses a smart approach to avoid testing all 2^16 possible combinations while still finding optimal recipes.\n\n"
        help_text += "Note: Calculation may take a few seconds for all products. For faster results, select a specific product."
        
        ttk.Label(help_frame, text=help_text, wraplength=800, justify=tk.LEFT).pack(pady=10, padx=10, fill=tk.X)
        
        # Create tooltip for equipment info
        self.equipment_tooltip_window = None
    
    def show_equipment_tooltip(self, event):
        """Show tooltip about equipment limitations"""
        x, y, _, _ = event.widget.bbox("insert")
        x += event.widget.winfo_rootx() + 25
        y += event.widget.winfo_rooty() + 20
        
        # Create a toplevel window
        self.equipment_tooltip_window = tk.Toplevel(self.root)
        self.equipment_tooltip_window.wm_overrideredirect(True)
        self.equipment_tooltip_window.wm_geometry(f"+{x}+{y}")
        
        # Create label in tooltip
        tooltip_frame = ttk.Frame(self.equipment_tooltip_window, relief='solid', borderwidth=1)
        tooltip_frame.pack(ipadx=5, ipady=5)
        
        label = ttk.Label(tooltip_frame, 
                         text="Limit the maximum number of mixers in recipes\n"
                              "to match your available equipment in-game.\n"
                              "Each mixer requires a separate machine to process.",
                         background=self.mid_green,
                         foreground=self.text_color,
                         justify=tk.LEFT,
                         wraplength=250)
        label.pack(ipadx=5, ipady=5)
    
    def hide_equipment_tooltip(self, event):
        """Hide the equipment tooltip"""
        if self.equipment_tooltip_window:
            self.equipment_tooltip_window.destroy()
            self.equipment_tooltip_window = None
    
    def calculate_top_recipes(self):
        """Calculate and display the top recipes for selected product(s)"""
        from src.calculator import find_top_profit_recipes, find_all_top_recipes
        
        selected_product = self.top_recipe_product_var.get()
        top_n = self.top_n_var.get()
        max_mixers = self.max_mixers_var.get()  # Get the maximum mixer limit
        
        # Clear existing tabs
        for tab in self.top_recipes_notebook.tabs():
            self.top_recipes_notebook.forget(tab)
        
        # Show progress
        mixer_limit_text = f"with max {max_mixers} mixers" if max_mixers < 8 else ""
        self.progress_var.set(f"Calculating top recipes {mixer_limit_text}... This may take a moment.")
        self.root.update()
        
        try:
            # Calculate top recipes
            if (selected_product == "All Products"):
                self.progress_var.set(f"Calculating for all products {mixer_limit_text} (this will take longer)...")
                self.root.update()
                
                # Calculate for all products with mixer limit
                all_results = find_all_top_recipes(top_n=top_n, max_mixers=max_mixers)
                
                # Create a tab for each product
                for product, recipes in all_results.items():
                    self.add_product_tab(product, recipes)
                
            else:
                # Calculate for just one product with mixer limit
                recipes = find_top_profit_recipes(selected_product, top_n=top_n, max_mixers=max_mixers)
                self.add_product_tab(selected_product, recipes)
            
            # Update progress message to include mixer limit if applicable
            if max_mixers < 8:
                self.progress_var.set(f"Calculation complete. Showing top {top_n} recipes with max {max_mixers} mixers.")
            else:
                self.progress_var.set(f"Calculation complete. Showing top {top_n} recipes.")
            
        except Exception as e:
            self.progress_var.set(f"Error calculating recipes: {str(e)}")
            messagebox.showerror("Calculation Error", f"An error occurred: {str(e)}")
    
    def add_product_tab(self, product, recipes):
        """Add a tab for a specific product with its top recipes"""
        # Create a new tab
        tab = ttk.Frame(self.top_recipes_notebook)
        self.top_recipes_notebook.add(tab, text=product)
        
        # Table for recipes
        columns = ("Rank", "Profit Margin", "Profit", "Market Value", "Cost", "# Mixers")
        recipe_tree = ttk.Treeview(tab, columns=columns, show="headings", height=5)
        
        # Column headings
        for col in columns:
            recipe_tree.heading(col, text=col)
            width = 75 if col in ("Rank", "# Mixers") else 100
            recipe_tree.column(col, width=width)
        
        # Add recipes to table
        for i, recipe in enumerate(recipes, 1):
            recipe_tree.insert("", tk.END, iid=f"{product}_{i}", values=(
                i, 
                f"{recipe['profit_margin']:.1f}%", 
                f"${recipe['profit']}", 
                f"${recipe['market_value']}", 
                f"${recipe['total_cost']}", 
                len(recipe['mixers'])
            ))
        
        recipe_tree.pack(fill=tk.X, pady=5)
        
        # Add selection handler
        recipe_tree.bind("<<TreeviewSelect>>", lambda e, p=product, r=recipes: self.show_recipe_details(e, p, r))
        
        # Details section
        ttk.Label(tab, text="Recipe Details:", font=("Arial", 11, "bold")).pack(anchor=tk.W, pady=(10, 5))
        
        details_frame = ttk.Frame(tab)
        details_frame.pack(fill=tk.BOTH, expand=True)
        
        # Left side: Mixing steps
        steps_frame = ttk.LabelFrame(details_frame, text="Mixing Steps")
        steps_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        steps_text = scrolledtext.ScrolledText(steps_frame, width=40, height=15, wrap=tk.WORD)
        steps_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        steps_text.insert(tk.END, "Select a recipe to view mixing steps")
        self._configure_scrolledtext(steps_text)  # Apply theme to text widget
        setattr(tab, "steps_text", steps_text)  # Store reference as attribute of tab
        
        # Right side: Effects
        effects_frame = ttk.LabelFrame(details_frame, text="Effects Applied")
        effects_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        effects_text = scrolledtext.ScrolledText(effects_frame, width=40, height=15, wrap=tk.WORD)
        effects_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        effects_text.insert(tk.END, "Select a recipe to view effects")
        self._configure_scrolledtext(effects_text)  # Apply theme to text widget
        setattr(tab, "effects_text", effects_text)  # Store reference as attribute of tab
    
    def show_recipe_details(self, event, product, recipes):
        """Show details for the selected recipe"""
        tree = event.widget
        selection = tree.selection()
        if not selection:
            return
        
        # Extract rank from the selected item's ID
        item_id = selection[0]
        rank = int(item_id.split('_')[1])
        
        # Get the recipe
        recipe = recipes[rank-1]
        
        # Get the tab
        tab_id = self.top_recipes_notebook.select()
        tab = self.top_recipes_notebook.nametowidget(tab_id)
        
        # Update steps text
        steps_text = getattr(tab, "steps_text")
        steps_text.delete(1.0, tk.END)
        
        steps_text.insert(tk.END, f"Base Product: {product}\n\n")
        steps_text.insert(tk.END, "Mixing Steps:\n")
        
        if not recipe['mixers']:
            steps_text.insert(tk.END, "No mixers needed (base product only)")
        else:
            for i, mixer in enumerate(recipe['mixers'], 1):
                steps_text.insert(tk.END, f"{i}. Add {mixer} (${MIXERS[mixer]['cost']})\n")
        
        steps_text.insert(tk.END, f"\nTotal Mixer Cost: ${sum(MIXERS[m]['cost'] for m in recipe['mixers'])}")
        
        # Update effects text
        effects_text = getattr(tab, "effects_text")
        effects_text.delete(1.0, tk.END)
        
        effects_text.insert(tk.END, f"Effects ({len(recipe['effects'])}/8):\n\n")
        
        # Calculate total multiplier
        total_multiplier = 0
        
        for effect in recipe['effects']:
            multiplier = EFFECTS[effect]["multiplier"]
            total_multiplier += multiplier
            effects_text.insert(tk.END, f"• {effect} (+{multiplier})\n")
        
        effects_text.insert(tk.END, f"\nTotal Multiplier: +{total_multiplier:.2f}")
        
        # Add summary
        effects_text.insert(tk.END, f"\n\nMarket Value: ${recipe['market_value']}")
        effects_text.insert(tk.END, f"\nTotal Cost: ${recipe['total_cost']}")
        effects_text.insert(tk.END, f"\nProfit: ${recipe['profit']}")
        effects_text.insert(tk.END, f"\nProfit Margin: {recipe['profit_margin']:.1f}%")
    
    def update_top_recipes_display(self, event=None):
        """Update the top recipes display when product selection changes"""
        # Just update the prompt
        if self.top_recipe_product_var.get() == "All Products":
            self.progress_var.set("Click 'Calculate Top Recipes' to find the best recipes for all products")
        else:
            self.progress_var.set(f"Click 'Calculate Top Recipes' to find the best recipes for {self.top_recipe_product_var.get()}")
    
    def update_top_recipes(self):
        """Update the top recipes content"""
        self.top_recipes_text.delete(1.0, tk.END)
        
        # Example top recipes content
        top_recipes = [
            "Recipe 1: Base Product A + Mixer X + Mixer Y",
            "Recipe 2: Base Product B + Mixer Z + Mixer W",
            "Recipe 3: Base Product C + Mixer V + Mixer U",
        ]
        
        for recipe in top_recipes:
            self.top_recipes_text.insert(tk.END, f"{recipe}\n\n")
    
    def setup_data_tab(self):
        """Setup the data tab for viewing game data"""
        frame = ttk.Frame(self.data_tab, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Tab for different data types
        data_notebook = ttk.Notebook(frame)
        data_notebook.pack(fill=tk.BOTH, expand=True)
        
        # Products tab
        products_frame = ttk.Frame(data_notebook)
        data_notebook.add(products_frame, text="Products")
        
        # Configure products frame for responsive sizing
        products_frame.columnconfigure(0, weight=1)
        
        # Table for base products
        ttk.Label(products_frame, text="Base Products:", font=("Arial", 12, "bold")).pack(anchor=tk.W, pady=5)
        
        # Create frames to hold tables and scrollbars
        base_products_frame = ttk.Frame(products_frame)
        base_products_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        products_columns = ("Product", "Base Value")
        products_tree = ttk.Treeview(base_products_frame, columns=products_columns, show="headings", height=4)
        
        # Add scrollbar to base products table
        base_products_scrollbar = ttk.Scrollbar(base_products_frame, orient=tk.VERTICAL, command=products_tree.yview)
        products_tree.configure(yscroll=base_products_scrollbar.set)
        
        base_products_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        products_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        for col in products_columns:
            products_tree.heading(col, text=col)
            products_tree.column(col, width=150)
        
        for product, value in BASE_MARKET_VALUES.items():
            products_tree.insert("", tk.END, values=(product, f"${value}"))
        
        # Table for marijuana strains
        ttk.Label(products_frame, text="Marijuana Strains:", font=("Arial", 12, "bold")).pack(anchor=tk.W, pady=5)
        
        # Create frame for strains table and scrollbar
        strains_frame = ttk.Frame(products_frame)
        strains_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        strains_columns = ("Strain", "Inherent Effect", "Seed Cost")
        strains_tree = ttk.Treeview(strains_frame, columns=strains_columns, show="headings", height=5)
        
        # Add scrollbar to strains table
        strains_scrollbar = ttk.Scrollbar(strains_frame, orient=tk.VERTICAL, command=strains_tree.yview)
        strains_tree.configure(yscroll=strains_scrollbar.set)
        
        strains_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        strains_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        for col in strains_columns:
            strains_tree.heading(col, text=col)
            strains_tree.column(col, width=150)
        
        for strain, info in MARIJUANA_STRAINS.items():
            strains_tree.insert("", tk.END, values=(strain, info["effect"], f"${info['seed_cost']}"))
        
        # Mixers tab
        mixers_frame = ttk.Frame(data_notebook)
        data_notebook.add(mixers_frame, text="Mixers")
        
        # Configure mixers frame for responsive sizing
        mixers_frame.columnconfigure(0, weight=1)
        mixers_frame.rowconfigure(0, weight=1)
        
        # Create frame for mixer table and scrollbar
        mixer_table_frame = ttk.Frame(mixers_frame)
        mixer_table_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        mixer_columns = ("Mixer", "Effect", "Cost")
        mixer_tree = ttk.Treeview(mixer_table_frame, columns=mixer_columns, show="headings", height=20)
        
        # Add scrollbar to mixer table
        mixer_scrollbar = ttk.Scrollbar(mixer_table_frame, orient=tk.VERTICAL, command=mixer_tree.yview)
        mixer_tree.configure(yscrollcommand=mixer_scrollbar.set)
        
        mixer_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        mixer_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        for col in mixer_columns:
            mixer_tree.heading(col, text=col)
            mixer_tree.column(col, width=150)
        
        for mixer, info in sorted(MIXERS.items()):
            mixer_tree.insert("", tk.END, values=(mixer, info["effect"], f"${info['cost']}"))
        
        # Effects tab
        effects_frame = ttk.Frame(data_notebook)
        data_notebook.add(effects_frame, text="Effects")
        
        # Configure effects frame for responsive sizing
        effects_frame.columnconfigure(0, weight=1)
        effects_frame.rowconfigure(0, weight=1)
        
        # Create frame for effects table and scrollbar
        effect_table_frame = ttk.Frame(effects_frame)
        effect_table_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        effect_columns = ("Effect", "Value Multiplier", "Addictiveness", "Tier")
        effect_tree = ttk.Treeview(effect_table_frame, columns=effect_columns, show="headings", height=20)
        
        # Add scrollbar to effects table
        effect_scrollbar = ttk.Scrollbar(effect_table_frame, orient=tk.VERTICAL, command=effect_tree.yview)
        effect_tree.configure(yscroll=effect_scrollbar.set)
        
        effect_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        effect_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        for col in effect_columns:
            effect_tree.heading(col, text=col)
            effect_tree.column(col, width=150)
        
        # Sort effects by tier and then by multiplier
        sorted_effects = sorted(EFFECTS.items(), key=lambda x: (x[1]["tier"], -x[1]["multiplier"]))
        for effect, info in sorted_effects:
            effect_tree.insert("", tk.END, values=(
                effect, 
                f"+{info['multiplier']:.2f}", 
                f"{info['addictiveness']:.3f}", 
                info["tier"]
            ))
    
    def calculate_single_mix(self):
        """Calculate profit for a single mix from user inputs"""
        base_product = self.base_var.get()
        
        # Get mixers in order
        mixers = self.mixer_order
        
        # Calculate profit metrics with enhanced accuracy
        market_value, total_cost, profit, profit_margin, effects, addictiveness = calculate_profit(base_product, mixers)
        
        # Update status bar with appropriate message based on whether mixers were used
        if mixers:
            self.update_status(f"Calculated profit for '{self.mix_name_var.get()}': ${profit} (Margin: {profit_margin:.1f}%)")
        else:
            self.update_status(f"Calculated base value for '{base_product}': ${market_value} (No mixers)")
        
        # Display results
        self.results_text.delete(1.0, tk.END)
        self.results_text.insert(tk.END, f"Mix: {self.mix_name_var.get()}\n")
        self.results_text.insert(tk.END, f"Base Product: {base_product}\n\n")
        
        self.results_text.insert(tk.END, f"Effects Applied ({len(effects)}/8):\n")
        if effects:
            for effect in effects:
                if effect in EFFECTS:
                    self.results_text.insert(tk.END, f"- {effect} (+{EFFECTS[effect]['multiplier']}, {EFFECTS[effect]['addictiveness']*100:.0f}% addictive)\n")
                else:
                    self.results_text.insert(tk.END, f"- {effect}\n")
        else:
            self.results_text.insert(tk.END, f"- None (base product only)\n")
        
        self.results_text.insert(tk.END, f"\nTotal Mixes: {len(mixers)}\n")
        self.results_text.insert(tk.END, f"Total Mixer Cost: ${sum(MIXERS[m]['cost'] for m in mixers) if mixers else 0}\n\n")
        
        self.results_text.insert(tk.END, f"Market Value: ${market_value}\n")
        self.results_text.insert(tk.END, f"Total Cost: ${total_cost}\n")
        self.results_text.insert(tk.END, f"Profit: ${profit}\n")
        self.results_text.insert(tk.END, f"Profit Margin: {profit_margin:.1f}%\n")
        self.results_text.insert(tk.END, f"Addictiveness: {addictiveness*100:.0f}%\n")
    
    def save_mix(self):
        """Save the current mix to compare later"""
        base_product = self.base_var.get()
        
        # Get mixers in order
        mixers = self.mixer_order
        
        # Allow saving even with no mixers (for base product comparison)
        # Save the mix
        self.user_mixes.append({
            'name': self.mix_name_var.get() if mixers else f"Base {base_product} (No Mixers)",
            'base_product': base_product,
            'mixers': mixers
        })
        
        # Update status bar with appropriate message
        if mixers:
            self.update_status(f"Mix '{self.mix_name_var.get()}' saved - now you have {len(self.user_mixes)} mixes available for comparison")
            msg = f"'{self.mix_name_var.get()}' has been saved and can be compared with other mixes."
        else:
            self.update_status(f"Base product '{base_product}' saved for comparison - now you have {len(self.user_mixes)} mixes available")
            msg = f"Base '{base_product}' (no mixers) has been saved and can be compared with other mixes."
        
        messagebox.showinfo("Mix Saved", msg)
    
    def update_recipe_details(self, event=None):
        """Update recipe details when selection changes"""
        recipe_name = self.recipe_var.get()
        recipe = RECIPES[recipe_name]
        
        self.recipe_details.delete(1.0, tk.END)
        self.recipe_details.insert(tk.END, f"Recipe: {recipe_name}\n\n")
        
        self.recipe_details.insert(tk.END, f"Base Products: {', '.join(recipe['base'])}\n\n")
        
        self.recipe_details.insert(tk.END, "Mixing Steps:\n")
        for i, mixer in enumerate(recipe['mixers'], 1):
            self.recipe_details.insert(tk.END, f"{i}. Add {mixer} (${MIXERS[mixer]['cost']})\n")
        
        self.recipe_details.insert(tk.END, f"\nTotal Mixes: {len(recipe['mixers'])}\n")
        self.recipe_details.insert(tk.END, f"Total Mixer Cost: ${sum(MIXERS[m]['cost'] for m in recipe['mixers'])}\n\n")
        
        # Calculate effects from mixers
        self.recipe_details.insert(tk.END, "Effects Applied:\n")
        for base in recipe['base']:
            effects = get_effects_from_mixers(base, recipe['mixers'])
            self.recipe_details.insert(tk.END, f"\nFor {base}:\n")
            for effect in effects:
                self.recipe_details.insert(tk.END, f"- {effect} (+{EFFECTS[effect]['multiplier']})\n")
    
    def calculate_recipe(self):
        """Calculate profit for selected recipe"""
        recipe_name = self.recipe_var.get()
        recipe = RECIPES[recipe_name]
        
        # Calculate for each base product
        self.recipe_details.delete(1.0, tk.END)
        self.recipe_details.insert(tk.END, f"Recipe: {recipe_name}\n\n")
        
        for base in recipe['base']:
            market_value, total_cost, profit, profit_margin, effects = calculate_profit(
                base, recipe['mixers']
            )
            
            self.recipe_details.insert(tk.END, f"Results for {base}:\n")
            self.recipe_details.insert(tk.END, f"Market Value: ${market_value}\n")
            self.recipe_details.insert(tk.END, f"Total Cost: ${total_cost}\n")
            self.recipe_details.insert(tk.END, f"Profit: ${profit}\n")
            self.recipe_details.insert(tk.END, f"Profit Margin: {profit_margin:.1f}%\n\n")
            
            self.recipe_details.insert(tk.END, "Effects Applied:\n")
            for effect in effects:
                self.recipe_details.insert(tk.END, f"- {effect} (+{EFFECTS[effect]['multiplier']})\n")
            
            self.recipe_details.insert(tk.END, "\n")
    
    def compare_all_mixes(self):
        """Compare all saved and predefined mixes"""
        # Clear current data
        for row in self.compare_tree.get_children():
            self.compare_tree.delete(row)
        
        # Prepare list of mixes to compare
        all_mixes = self.user_mixes.copy()
        
        # Add predefined recipes
        for recipe_name, recipe in RECIPES.items():
            for base in recipe['base']:
                all_mixes.append({
                    'name': f"{recipe_name} ({base})",
                    'base_product': base,
                    'mixers': recipe['mixers']
                })
        
        # Compare mixes
        results = compare_mixes(all_mixes)
        
        # Display in table
        for i, mix in enumerate(results):
            self.compare_tree.insert("", tk.END, iid=str(i), values=(
                mix['name'],
                mix['base_product'],
                f"${mix['market_value']}",
                f"${mix['total_cost']}",
                f"${mix['profit']}",
                f"{mix['profit_margin']:.1f}%",
                mix['num_mixes']
            ))
    
    def show_selected_mix_details(self, event=None):
        """Show details for the selected mix in comparison view"""
        selected_items = self.compare_tree.selection()
        if not selected_items:
            return
        
        # Get index of selected mix
        index = int(selected_items[0])
        
        # Compare to get full mix details
        all_mixes = self.user_mixes.copy()
        for recipe_name, recipe in RECIPES.items():
            for base in recipe['base']:
                all_mixes.append({
                    'name': f"{recipe_name} ({base})",
                    'base_product': base,
                    'mixers': recipe['mixers']
                })
        
        results = compare_mixes(all_mixes)
        mix = results[index]
        
        # Display details
        self.compare_details.delete(1.0, tk.END)
        self.compare_details.insert(tk.END, f"Mix: {mix['name']}\n")
        self.compare_details.insert(tk.END, f"Base Product: {mix['base_product']}\n")
        
        # Add yield information for marijuana strains
        from src.game_data import MARIJUANA_STRAINS, PRODUCTION_INFO
        if mix['base_product'] in MARIJUANA_STRAINS:
            min_yield, max_yield = MARIJUANA_STRAINS[mix['base_product']]["yield_range"]
            self.compare_details.insert(tk.END, f"Yield per seed: {min_yield}-{max_yield} buds\n")
            self.compare_details.insert(tk.END, f"Seed Cost: ${MARIJUANA_STRAINS[mix['base_product']]['seed_cost']}\n")
            
            # Calculate cost per bud with proper rounding
            cost_per_bud = MARIJUANA_STRAINS[mix['base_product']]['seed_cost']/((min_yield + max_yield)/2)
            self.compare_details.insert(tk.END, f"Cost per bud: ${cost_per_bud:.0f}\n")
        elif mix['base_product'] in PRODUCTION_INFO:
            # Add batch production info for meth and cocaine
            yield_amount = PRODUCTION_INFO[mix['base_product']]["yield"]
            ingredients_cost = PRODUCTION_INFO[mix['base_product']]["ingredients_cost"]
            self.compare_details.insert(tk.END, f"Yield per batch: {yield_amount} units\n")
            self.compare_details.insert(tk.END, f"Batch Cost: ${ingredients_cost}\n")
            
            # Calculate unit cost with proper rounding
            unit_cost = ingredients_cost/yield_amount
            self.compare_details.insert(tk.END, f"Cost per unit: ${unit_cost:.0f}\n")
        
        self.compare_details.insert(tk.END, f"\nEffects Applied ({len(mix['effects'])}/8):\n")
        for effect in mix['effects']:
            if effect in EFFECTS:
                self.compare_details.insert(tk.END, f"- {effect} (+{EFFECTS[effect]['multiplier']}, {EFFECTS[effect]['addictiveness']*100:.0f}% addictive)\n")
            else:
                self.compare_details.insert(tk.END, f"- {effect}\n")
        
        self.compare_details.insert(tk.END, f"\nMixers Used ({mix['num_mixes']}):\n")
        
        # Count mixer occurrences
        mixer_counts = {}
        for mixer in mix['mixers']:
            mixer_counts[mixer] = mixer_counts.get(mixer, 0) + 1
        
        for mixer, count in mixer_counts.items():
            self.compare_details.insert(tk.END, f"- {mixer} x{count} (${MIXERS[mixer]['cost'] * count})\n")
        
        # Display values with proper integer formatting
        self.compare_details.insert(tk.END, f"\nMarket Value: ${mix['market_value']}\n")
        self.compare_details.insert(tk.END, f"Production Cost: ${mix['total_cost']}\n")
        self.compare_details.insert(tk.END, f"Profit: ${mix['profit']}\n")
        self.compare_details.insert(tk.END, f"Profit Margin: {mix['profit_margin']:.1f}%\n")
        
        # Add addictiveness information to the details view if available
        if 'addictiveness' in mix:
            self.compare_details.insert(tk.END, f"Addictiveness: {mix['addictiveness']*100:.0f}%\n")
    
    def update_status_on_tab_change(self, event):
        """Update the status bar when the tab changes"""
        selected_tab = event.widget.tab(event.widget.select(), "text")
        
        # Set appropriate message based on selected tab
        if (selected_tab == "Calculator"):
            self.status_var.set("Calculator Tab: Create and evaluate custom drug mixes")
        elif (selected_tab == "Recipes"):
            self.status_var.set("Recipes Tab: View and calculate profit for predefined recipes")
        elif (selected_tab == "Compare"):
            self.status_var.set(f"Compare Tab: {len(self.user_mixes)} saved mixes ready for comparison")
        elif (selected_tab == "Top Recipes"):
            self.status_var.set("Top Recipes Tab: Find the most profitable recipes")
        elif (selected_tab == "Game Data"):
            self.status_var.set("Game Data Tab: Browse all game items, effects, and values")
        elif (selected_tab == "Customers"):
            self.status_var.set(f"Customers Tab: {len(self.customer_data.get('customers', []))} customers in database")
        else:
            self.status_var.set(f"Selected Tab: {selected_tab}")
            
    def update_status(self, message):
        """Update the status bar with a custom message"""
        self.status_var.set(message)

    def load_customer_data(self):
        """Load existing customer data from file"""
        if os.path.exists(self.customer_data_file):
            try:
                with open(self.customer_data_file, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return {"customers": []}
        return {"customers": []}
    
    def save_customer_data(self):
        """Save customer data to file"""
        with open(self.customer_data_file, 'w') as f:
            json.dump(self.customer_data, f, indent=4)
        messagebox.showinfo("Success", "Customer data saved successfully!")
    
    def setup_customers_tab(self):
        """Setup the Customers tab for viewing and managing customer data"""
        frame = ttk.Frame(self.customers_tab, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Split frame into left and right sections
        left_frame = ttk.Frame(frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        right_frame = ttk.Frame(frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        # Left panel (customer list and filters)
        ttk.Label(left_frame, text="Customers:", style="Subtitle.TLabel").pack(anchor=tk.W, pady=(0, 5))
        
        # Filter controls
        filter_frame = ttk.Frame(left_frame)
        filter_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(filter_frame, text="Search:").pack(side=tk.LEFT, padx=5)
        self.customer_search_var = tk.StringVar()
        search_entry = ttk.Entry(filter_frame, textvariable=self.customer_search_var, width=20)
        search_entry.pack(side=tk.LEFT, padx=5)
        search_entry.bind("<KeyRelease>", self.filter_customers)
        
        # Region filter
        ttk.Label(filter_frame, text="Region:").pack(side=tk.LEFT, padx=(10, 5))
        self.customer_region_var = tk.StringVar(value="All")
        region_combo = ttk.Combobox(filter_frame, textvariable=self.customer_region_var, width=15, state="readonly")
        region_combo['values'] = ["All"] + self.get_unique_regions()
        region_combo.pack(side=tk.LEFT, padx=5)
        region_combo.bind("<<ComboboxSelected>>", self.filter_customers)
        
        # Standards filter
        ttk.Label(filter_frame, text="Standards:").pack(side=tk.LEFT, padx=(10, 5))
        self.customer_standards_var = tk.StringVar(value="All")
        standards_combo = ttk.Combobox(filter_frame, textvariable=self.customer_standards_var, width=10, state="readonly")
        standards_combo['values'] = ["All", "Low", "Medium", "High"]
        standards_combo.pack(side=tk.LEFT, padx=5)
        standards_combo.bind("<<ComboboxSelected>>", self.filter_customers)
        
        # Effects filter
        ttk.Label(filter_frame, text="Effect:").pack(side=tk.LEFT, padx=(10, 5))
        self.customer_effect_var = tk.StringVar(value="All")
        effects_combo = ttk.Combobox(filter_frame, textvariable=self.customer_effect_var, width=15, state="readonly")
        effects_combo['values'] = ["All"] + sorted(list(EFFECTS.keys()))
        effects_combo.pack(side=tk.LEFT, padx=5)
        effects_combo.bind("<<ComboboxSelected>>", self.filter_customers)
        
        # Customer list
        list_frame = ttk.Frame(left_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        columns = ("Name", "Region", "Standards", "Favorite Effects")
        self.customer_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=20)
        
        # Configure columns
        self.customer_tree.column("Name", width=120)
        self.customer_tree.column("Region", width=100)
        self.customer_tree.column("Standards", width=80)
        self.customer_tree.column("Favorite Effects", width=200)
        
        # Add headings with sort functionality
        for col in columns:
            self.customer_tree.heading(col, text=col, command=lambda c=col: self.sort_customers_by_column(c))
        
        # Add scrollbar
        tree_scroll = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.customer_tree.yview)
        self.customer_tree.configure(yscrollcommand=tree_scroll.set)
        
        # Layout
        self.customer_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind selection event to show details
        self.customer_tree.bind("<<TreeviewSelect>>", self.show_customer_details)
        
        # List actions
        list_actions_frame = ttk.Frame(left_frame)
        list_actions_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(list_actions_frame, text="Add New", command=self.create_new_customer).pack(side=tk.LEFT, padx=5)
        ttk.Button(list_actions_frame, text="Delete", command=self.delete_customer).pack(side=tk.LEFT, padx=5)
        ttk.Button(list_actions_frame, text="Refresh", command=self.refresh_customer_list).pack(side=tk.LEFT, padx=5)
        
        # Right panel (customer details)
        ttk.Label(right_frame, text="Customer Details:", style="Subtitle.TLabel").pack(anchor=tk.W, pady=(0, 5))
        
        # Customer editor
        details_frame = ttk.Frame(right_frame)
        details_frame.pack(fill=tk.BOTH, expand=True)
        
        # Basic info
        basic_frame = ttk.LabelFrame(details_frame, text="Basic Information")
        basic_frame.pack(fill=tk.X, pady=5)
        
        info_grid = ttk.Frame(basic_frame)
        info_grid.pack(fill=tk.X, padx=10, pady=5)
        
        # Name, Region, Standards
        ttk.Label(info_grid, text="Name:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.customer_name_var = tk.StringVar()
        ttk.Entry(info_grid, textvariable=self.customer_name_var, width=30).grid(row=0, column=1, sticky=tk.W, padx=5, pady=2)
        
        ttk.Label(info_grid, text="Region:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        self.customer_region_edit_var = tk.StringVar()
        ttk.Entry(info_grid, textvariable=self.customer_region_edit_var, width=30).grid(row=1, column=1, sticky=tk.W, padx=5, pady=2)
        
        ttk.Label(info_grid, text="Standards:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=2)
        self.customer_standards_edit_var = tk.StringVar()
        standards_combo = ttk.Combobox(info_grid, textvariable=self.customer_standards_edit_var, width=15, values=["Low", "Medium", "High"])
        standards_combo.grid(row=2, column=1, sticky=tk.W, padx=5, pady=2)
        
        # Favorite effects
        effects_frame = ttk.LabelFrame(details_frame, text="Favorite Effects")
        effects_frame.pack(fill=tk.X, pady=5)
        
        self.customer_effects_text = scrolledtext.ScrolledText(effects_frame, height=3, width=40, wrap=tk.WORD)
        self.customer_effects_text.pack(fill=tk.X, padx=10, pady=5)
        self._configure_scrolledtext(self.customer_effects_text)
        
        # Residency and work
        locations_frame = ttk.LabelFrame(details_frame, text="Locations")
        locations_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(locations_frame, text="Residency:").pack(anchor=tk.W, padx=10, pady=(5, 0))
        self.customer_residency_text = scrolledtext.ScrolledText(locations_frame, height=2, width=40, wrap=tk.WORD)
        self.customer_residency_text.pack(fill=tk.X, padx=10, pady=5)
        self._configure_scrolledtext(self.customer_residency_text)
        
        ttk.Label(locations_frame, text="Work:").pack(anchor=tk.W, padx=10, pady=(5, 0))
        self.customer_work_text = scrolledtext.ScrolledText(locations_frame, height=2, width=40, wrap=tk.WORD)
        self.customer_work_text.pack(fill=tk.X, padx=10, pady=5)
        self._configure_scrolledtext(self.customer_work_text)
        
        # Relations
        relations_frame = ttk.LabelFrame(details_frame, text="Relations")
        relations_frame.pack(fill=tk.X, pady=5)
        
        self.customer_relations_text = scrolledtext.ScrolledText(relations_frame, height=3, width=40, wrap=tk.WORD)
        self.customer_relations_text.pack(fill=tk.X, padx=10, pady=5)
        self._configure_scrolledtext(self.customer_relations_text)
        
        # Notes
        notes_frame = ttk.LabelFrame(details_frame, text="Notes")
        notes_frame.pack(fill=tk.X, pady=5)
        
        self.customer_notes_text = scrolledtext.ScrolledText(notes_frame, height=3, width=40, wrap=tk.WORD)
        self.customer_notes_text.pack(fill=tk.X, padx=10, pady=5)
        self._configure_scrolledtext(self.customer_notes_text)
        
        # Action buttons
        action_frame = ttk.Frame(details_frame)
        action_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(action_frame, text="Save Changes", command=self.save_customer).pack(side=tk.RIGHT, padx=5)
        ttk.Button(action_frame, text="Clear Form", command=self.clear_customer_form).pack(side=tk.RIGHT, padx=5)
        
        # Wiki importer section
        importer_frame = ttk.LabelFrame(right_frame, text="Wiki Data Import")
        importer_frame.pack(fill=tk.X, pady=10)
        
        # URL input
        url_frame = ttk.Frame(importer_frame)
        url_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(url_frame, text="Wiki URL:").pack(side=tk.LEFT, padx=5)
        self.wiki_url_var = tk.StringVar()
        ttk.Entry(url_frame, textvariable=self.wiki_url_var, width=50).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        ttk.Button(url_frame, text="Fetch", command=self.fetch_customer_data).pack(side=tk.LEFT, padx=5)
        
        # Bulk import controls
        bulk_frame = ttk.Frame(importer_frame)
        bulk_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(bulk_frame, text="Bulk Import:").pack(side=tk.LEFT, padx=5)
        ttk.Button(bulk_frame, text="Import All Customers", command=self.import_all_customers).pack(side=tk.LEFT, padx=5)
        
        # Initialize the customer list
        self.refresh_customer_list()
        
        # Update status bar when entering this tab
        self.update_status(f"Customer Database: {len(self.customer_data.get('customers', []))} customers loaded")
        
    def get_unique_regions(self):
        """Get a list of unique regions from the customer data"""
        regions = set()
        for customer in self.customer_data.get("customers", []):
            if customer.get("region"):
                regions.add(customer.get("region"))
        return sorted(list(regions))
    
    def refresh_customer_list(self):
        """Refresh the customer list view with all customers"""
        # Clear current items
        for item in self.customer_tree.get_children():
            self.customer_tree.delete(item)
        
        # Add all customers
        for i, customer in enumerate(self.customer_data.get("customers", [])):
            self.customer_tree.insert("", tk.END, iid=str(i), values=(
                customer.get("name", "Unknown"),
                customer.get("region", ""),
                customer.get("standards", ""),
                ", ".join(customer.get("favorite_effects", []))
            ))
            
        # Update region filter dropdown values
        # Instead of using winfo_descendants(), we'll directly find the combo box by traversing
        # the widget hierarchy in a more compatible way
        try:
            region_combo = None
            # Find all the children of the customers tab
            for child in self.customers_tab.winfo_children():
                # Look in each frame for the filter controls
                if isinstance(child, ttk.Frame):
                    for subchild in child.winfo_children():
                        if isinstance(subchild, ttk.Frame):
                            # This might be our filter frame
                            for filter_child in subchild.winfo_children():
                                # Check if this is a combobox with our region variable
                                if isinstance(filter_child, ttk.Combobox):
                                    try:
                                        if filter_child["textvariable"] == str(self.customer_region_var):
                                            region_combo = filter_child
                                            break
                                    except (KeyError, AttributeError):
                                        continue
            
            # If we found it, update its values
            if region_combo:
                region_combo["values"] = ["All"] + self.get_unique_regions()
        except Exception as e:
            print(f"Error updating region combobox: {e}")
            
        # Update status
        self.update_status(f"Customer Database: {len(self.customer_data.get('customers', []))} customers loaded")
    
    def filter_customers(self, event=None):
        """Filter the customer list based on the filter criteria"""
        search_text = self.customer_search_var.get().lower()
        region_filter = self.customer_region_var.get()
        standards_filter = self.customer_standards_var.get()
        effect_filter = self.customer_effect_var.get()
        
        # Clear current items
        for item in self.customer_tree.get_children():
            self.customer_tree.delete(item)
        
        # Add filtered customers
        count = 0
        for i, customer in enumerate(self.customer_data.get("customers", [])):
            # Check if customer matches all filters
            if search_text and not (
                search_text in customer.get("name", "").lower() or
                search_text in customer.get("region", "").lower() or
                search_text in ", ".join(customer.get("relations", [])).lower()
            ):
                continue
            
            if region_filter != "All" and customer.get("region") != region_filter:
                continue
                
            if standards_filter != "All" and customer.get("standards") != standards_filter:
                continue
                
            if effect_filter != "All" and effect_filter not in customer.get("favorite_effects", []):
                continue
            
            # Add to treeview
            self.customer_tree.insert("", tk.END, iid=str(i), values=(
                customer.get("name", "Unknown"),
                customer.get("region", ""),
                customer.get("standards", ""),
                ", ".join(customer.get("favorite_effects", []))
            ))
            count += 1
        
        # Update status with filter results
        filters_applied = []
        if search_text:
            filters_applied.append(f"search='{search_text}'")
        if region_filter != "All":
            filters_applied.append(f"region='{region_filter}'")
        if standards_filter != "All":
            filters_applied.append(f"standards='{standards_filter}'")
        if effect_filter != "All":
            filters_applied.append(f"effect='{effect_filter}'")
            
        if filters_applied:
            self.update_status(f"Showing {count} customers matching {', '.join(filters_applied)}")
        else:
            self.update_status(f"Showing all {count} customers")
    
    def show_customer_details(self, event=None):
        """Show details of the selected customer"""
        selected = self.customer_tree.selection()
        if not selected:
            return
            
        try:
            # Get the selected customer index
            customer_index = int(selected[0])
            customer = self.customer_data["customers"][customer_index]
            
            # Fill in details form
            self.customer_name_var.set(customer.get("name", ""))
            self.customer_region_edit_var.set(customer.get("region", ""))
            self.customer_standards_edit_var.set(customer.get("standards", ""))
            
            # Clear and populate text widgets
            self.customer_effects_text.delete(1.0, tk.END)
            self.customer_effects_text.insert(tk.END, ", ".join(customer.get("favorite_effects", [])))
            
            self.customer_residency_text.delete(1.0, tk.END)
            self.customer_residency_text.insert(tk.END, customer.get("residency", ""))
            
            self.customer_work_text.delete(1.0, tk.END)
            self.customer_work_text.insert(tk.END, customer.get("work", ""))
            
            self.customer_relations_text.delete(1.0, tk.END)
            self.customer_relations_text.insert(tk.END, ", ".join(customer.get("relations", [])))
            
            self.customer_notes_text.delete(1.0, tk.END)
            self.customer_notes_text.insert(tk.END, customer.get("notes", ""))
            
            # Update status
            self.update_status(f"Viewing customer: {customer.get('name')}")
            
        except (IndexError, ValueError) as e:
            # Handle errors in customer lookup
            print(f"Error showing customer details: {e}")
    
    def create_new_customer(self):
        """Create a new customer entry"""
        # Clear all form fields
        self.clear_customer_form()
        
        # Try to find and set focus to the name field
        try:
            # Look through frames to find the customer name entry
            for child in self.customers_tab.winfo_children():
                if isinstance(child, ttk.Frame):
                    for frame in child.winfo_children():
                        if isinstance(frame, ttk.Frame):
                            for detail_frame in frame.winfo_children():
                                if isinstance(detail_frame, ttk.LabelFrame):
                                    for grid_frame in detail_frame.winfo_children():
                                        for widget in grid_frame.winfo_children():
                                            if isinstance(widget, ttk.Entry):
                                                try:
                                                    if widget.cget("textvariable") == str(self.customer_name_var):
                                                        widget.focus_set()
                                                        break
                                                except (KeyError, AttributeError):
                                                    continue
        except Exception as e:
            print(f"Error setting focus: {e}")
            
        # Update status
        self.update_status("Creating new customer - fill in details and click Save")
    
    def clear_customer_form(self):
        """Clear all form fields"""
        self.customer_name_var.set("")
        self.customer_region_edit_var.set("")
        self.customer_standards_edit_var.set("")
        
        self.customer_effects_text.delete(1.0, tk.END)
        self.customer_residency_text.delete(1.0, tk.END)
        self.customer_work_text.delete(1.0, tk.END)
        self.customer_relations_text.delete(1.0, tk.END)
        self.customer_notes_text.delete(1.0, tk.END)
        
        # Clear selection in treeview
        self.customer_tree.selection_remove(self.customer_tree.selection())
    
    def save_customer(self):
        """Save the current customer data"""
        name = self.customer_name_var.get().strip()
        if not name:
            messagebox.showerror("Error", "Customer name is required")
            return
        
        # Get all form data
        customer_data = {
            "name": name,
            "region": self.customer_region_edit_var.get().strip(),
            "standards": self.customer_standards_edit_var.get().strip(),
            "favorite_effects": [e.strip() for e in self.customer_effects_text.get(1.0, tk.END).strip().split(",") if e.strip()],
            "residency": self.customer_residency_text.get(1.0, tk.END).strip(),
            "work": self.customer_work_text.get(1.0, tk.END).strip(),
            "relations": [r.strip() for r in self.customer_relations_text.get(1.0, tk.END).strip().split(",") if r.strip()],
            "notes": self.customer_notes_text.get(1.0, tk.END).strip()
        }
        
        # Check if we're updating an existing customer
        selected = self.customer_tree.selection()
        if selected:
            # Update existing customer
            try:
                customer_index = int(selected[0])
                self.customer_data["customers"][customer_index] = customer_data
                self.update_status(f"Updated customer: {name}")
            except (IndexError, ValueError):
                # Add as new if index lookup fails
                self.customer_data.setdefault("customers", []).append(customer_data)
                self.update_status(f"Added new customer: {name}")
        else:
            # Add new customer
            self.customer_data.setdefault("customers", []).append(customer_data)
            self.update_status(f"Added new customer: {name}")
        
        # Save to file and refresh the list
        self.save_customer_data()
        self.refresh_customer_list()
    
    def delete_customer(self):
        """Delete the selected customer"""
        selected = self.customer_tree.selection()
        if not selected:
            messagebox.showinfo("Info", "Please select a customer to delete")
            return
            
        try:
            customer_index = int(selected[0])
            customer = self.customer_data["customers"][customer_index]
            
            if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete {customer.get('name')}?"):
                # Remove from data
                del self.customer_data["customers"][customer_index]
                
                # Save and refresh
                self.save_customer_data()
                self.refresh_customer_list()
                
                # Clear form and update status
                self.clear_customer_form()
                self.update_status(f"Deleted customer: {customer.get('name')}")
                
        except (IndexError, ValueError) as e:
            print(f"Error deleting customer: {e}")
    
    def fetch_customer_data(self):
        """Fetch customer data from the provided wiki URL"""
        url = self.wiki_url_var.get().strip()
        if not url:
            messagebox.showerror("Error", "Please enter a valid URL")
            return
            
        try:
            self.update_status(f"Fetching customer data from {url}...")
            self.root.update()
            
            # Request the page with proper headers to avoid potential blocks
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            # Store HTML content for debugging
            html_content = response.text
            
            # Debug message
            print(f"Fetched page with status code: {response.status_code}, content length: {len(html_content)} bytes")
            
            # Parse with BeautifulSoup - use html.parser instead of the default
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Debug - print title to verify we have a valid page
            print(f"Page title: {soup.title.text if soup.title else 'No title found'}")
            
            # Extract customer name from title
            title = soup.find('title')
            name = title.text.split('|')[0].strip() if title else "Unknown"
            print(f"Extracted name: {name}")
            
            # Skip if this is the category page and not an actual customer
            if "Category:Customers" in name:
                messagebox.showerror("Error", "The URL provided is the Category page. Please use a specific customer page URL.")
                self.update_status("Error: Category page URL detected, not a customer page")
                return
            
            # Try different methods for data extraction
            customer_data = self._extract_customer_data_method1(soup)
            
            # If first method fails, try alternate approach
            if not customer_data["region"] and not customer_data["standards"] and not customer_data["favorite_effects"]:
                print("First extraction method failed, trying alternate method...")
                customer_data = self._extract_customer_data_method2(soup)
            
            # Populate form with extracted data
            self.customer_name_var.set(name)
            self.customer_region_edit_var.set(customer_data["region"])
            self.customer_standards_edit_var.set(customer_data["standards"])
            
            self.customer_effects_text.delete(1.0, tk.END)
            self.customer_effects_text.insert(tk.END, ", ".join(customer_data["favorite_effects"]))
            
            self.customer_residency_text.delete(1.0, tk.END)
            self.customer_residency_text.insert(tk.END, customer_data["residency"])
            
            self.customer_work_text.delete(1.0, tk.END)
            self.customer_work_text.insert(tk.END, customer_data["work"])
            
            self.customer_relations_text.delete(1.0, tk.END)
            self.customer_relations_text.insert(tk.END, ", ".join(customer_data["relations"]))
            
            # Add note about the source
            self.customer_notes_text.delete(1.0, tk.END)
            self.customer_notes_text.insert(tk.END, f"Imported from {url} on {datetime.datetime.now().strftime('%Y-%m-%d')}")
            
            self.update_status(f"Successfully fetched data for {name}")
            
        except Exception as e:
            self.update_status(f"Error fetching customer data: {str(e)}")
            messagebox.showerror("Error", f"Failed to fetch customer data: {str(e)}")
            print(f"Exception while fetching customer data: {e}")
            import traceback
            traceback.print_exc()

    def _extract_customer_data_method1(self, soup):
        """Extract customer data using method 1 - looking for div elements"""
        customer_data = {
            "region": "",
            "standards": "",
            "favorite_effects": [],
            "relations": [],
            "residency": "",
            "work": ""
        }
        
        # Extract region from infobox
        region_label = soup.find('div', string=lambda s: s and "Region" in s)
        if region_label:
            region_div = region_label.find_next_sibling('div')
            if region_div:
                customer_data["region"] = region_div.text.strip()
                print(f"Found region: {customer_data['region']}")
        
        # Extract standards level
        standards_label = soup.find('div', string=lambda s: s and "Standards" in s)
        if standards_label:
            standards_div = standards_label.find_next_sibling('div')
            if standards_div:
                standards_text = standards_div.text.strip()
                # Extract just the level (Low, Medium, High)
                if "Low" in standards_text:
                    customer_data["standards"] = "Low"
                elif "Medium" in standards_text:
                    customer_data["standards"] = "Medium"
                elif "High" in standards_text:
                    customer_data["standards"] = "High"
                print(f"Found standards: {customer_data['standards']}")
        
        # Extract favorite effects
        effects_label = soup.find('div', string=lambda s: s and ("Favourite Effects" in s or "Favorite Effects" in s))
        if effects_label:
            print("Found effects label")
            # Get all sibling divs until we reach the next section
            current = effects_label.find_next_sibling('div')
            while current and current.name == 'div' and not current.find('div', recursive=False):
                effect_text = current.text.strip()
                if effect_text and effect_text not in ["Relations", "Region", "Standards"]:
                    customer_data["favorite_effects"].append(effect_text)
                    print(f"Added effect: {effect_text}")
                current = current.find_next_sibling('div')
        
        # Extract relations
        relations_label = soup.find('div', string=lambda s: s and "Relations" in s)
        if relations_label:
            print("Found relations label")
            # Get all sibling divs until we reach the next section
            current = relations_label.find_next_sibling('div')
            while current and current.name == 'div' and not current.find('div', recursive=False):
                relation_text = current.text.strip()
                if relation_text and relation_text not in ["Region", "Standards"]:
                    customer_data["relations"].append(relation_text)
                    print(f"Added relation: {relation_text}")
                current = current.find_next_sibling('div')
        
        # Extract residency and work from section headings
        residency_heading = soup.find(['h2', 'h3', 'h4'], string=lambda s: s and "Residency" in s)
        if residency_heading:
            print("Found residency heading")
            # Try to find the paragraph after the heading
            next_elem = residency_heading.find_next()
            while next_elem and next_elem.name != 'h2' and next_elem.name != 'h3' and next_elem.name != 'h4':
                if next_elem.name == 'p':
                    customer_data["residency"] = next_elem.text.strip()
                    print(f"Found residency text: {customer_data['residency'][:30]}...")
                    break
                next_elem = next_elem.find_next()
        
        work_heading = soup.find(['h2', 'h3', 'h4'], string=lambda s: s and "Work" in s)
        if work_heading:
            print("Found work heading")
            # Try to find the paragraph after the heading
            next_elem = work_heading.find_next()
            while next_elem and next_elem.name != 'h2' and next_elem.name != 'h3' and next_elem.name != 'h4':
                if next_elem.name == 'p':
                    customer_data["work"] = next_elem.text.strip()
                    print(f"Found work text: {customer_data['work'][:30]}...")
                    break
                next_elem = next_elem.find_next()
        
        return customer_data

    def _extract_customer_data_method2(self, soup):
        """Extract customer data using method 2 - using more general selectors"""
        customer_data = {
            "region": "",
            "standards": "",
            "favorite_effects": [],
            "relations": [],
            "residency": "",
            "work": ""
        }
        
        # Look for data in any element with appropriate section indicators
        
        # Try to find region in any element
        region_elements = soup.find_all(string=lambda s: s and "Region:" in s)
        for element in region_elements:
            # Look for region value after the "Region:" label
            text = element.strip()
            if ":" in text:
                region_value = text.split(":", 1)[1].strip()
                if region_value:
                    customer_data["region"] = region_value
                    print(f"Method 2 - Found region: {customer_data['region']}")
                    break
        
        # Try to find standards in any element
        standards_elements = soup.find_all(string=lambda s: s and "Standards:" in s)
        for element in standards_elements:
            # Look for standards value
            text = element.strip()
            if "Low" in text:
                customer_data["standards"] = "Low"
            elif "Medium" in text:
                customer_data["standards"] = "Medium"
            elif "High" in text:
                customer_data["standards"] = "High"
            if customer_data["standards"]:
                print(f"Method 2 - Found standards: {customer_data['standards']}")
                break
        
        # Try to find favorite effects
        effects_elements = soup.find_all(string=lambda s: s and ("Favourite Effects:" in s or "Favorite Effects:" in s))
        for element in effects_elements:
            parent = element.parent
            # Try to find a list or paragraphs after this element
            effects_list = []
            
            # Try for list items first
            list_items = parent.find_next('ul')
            if list_items:
                for item in list_items.find_all('li'):
                    effects_list.append(item.text.strip())
                    print(f"Method 2 - Found effect in list: {item.text.strip()}")
            
            # If no list, look for comma-separated text after the label
            if not effects_list:
                text = element.strip()
                if ":" in text:
                    effects_text = text.split(":", 1)[1].strip()
                    if effects_text:
                        effects_list = [e.strip() for e in effects_text.split(",") if e.strip()]
                        print(f"Method 2 - Found effects in text: {effects_list}")
            
            if effects_list:
                customer_data["favorite_effects"] = effects_list
                break
        
        # Try to find relations
        relations_elements = soup.find_all(string=lambda s: s and "Relations:" in s)
        for element in relations_elements:
            parent = element.parent
            relations_list = []
            
            # Try for list items
            list_items = parent.find_next('ul')
            if list_items:
                for item in list_items.find_all('li'):
                    relations_list.append(item.text.strip())
                    print(f"Method 2 - Found relation in list: {item.text.strip()}")
            
            # If no list, look for comma-separated text
            if not relations_list:
                text = element.strip()
                if ":" in text:
                    relations_text = text.split(":", 1)[1].strip()
                    if relations_text:
                        relations_list = [r.strip() for r in relations_text.split(",") if r.strip()]
                        print(f"Method 2 - Found relations in text: {relations_list}")
            
            if relations_list:
                customer_data["relations"] = relations_list
                break
        
        # Try to find residency and work in paragraphs
        # First look for sections by any heading
        for section_label in ["Residency", "Work"]:
            # Try to find heading that contains our section label
            heading_elements = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5'], string=lambda s: s and section_label in s)
            
            if heading_elements:
                print(f"Method 2 - Found {section_label} heading")
                for heading in heading_elements:
                    next_p = heading.find_next('p')
                    if next_p:
                        if section_label == "Residency":
                            customer_data["residency"] = next_p.text.strip()
                            print(f"Method 2 - Found residency: {customer_data['residency'][:30]}...")
                        else:  # Work
                            customer_data["work"] = next_p.text.strip()
                            print(f"Method 2 - Found work: {customer_data['work'][:30]}...")
                        break
        
        # If still no residency/work, try looking for div sections
        if not customer_data["residency"]:
            residency_elements = soup.find_all(string=lambda s: s and "Residency:" in s)
            for element in residency_elements:
                text = element.strip()
                if ":" in text:
                    residency_text = text.split(":", 1)[1].strip()
                    if residency_text:
                        customer_data["residency"] = residency_text
                        print(f"Method 2 - Found residency from label: {customer_data['residency'][:30]}...")
                        break
        
        if not customer_data["work"]:
            work_elements = soup.find_all(string=lambda s: s and "Work:" in s)
            for element in work_elements:
                text = element.strip()
                if ":" in text:
                    work_text = text.split(":", 1)[1].strip()
                    if work_text:
                        customer_data["work"] = work_text
                        print(f"Method 2 - Found work from label: {customer_data['work'][:30]}...")
                        break
        
        return customer_data
    
    def import_all_customers(self):
        """Import all customers from the wiki category page"""
        # Ask for confirmation
        if not messagebox.askyesno("Confirm Import", "This will fetch data for all customers from the Schedule 1 wiki. The process may take several minutes. Continue?"):
            return
            
        try:
            # Create progress window
            progress_window = tk.Toplevel(self.root)
            progress_window.title("Importing Customers")
            progress_window.geometry("600x200")
            progress_window.transient(self.root)
            progress_window.grab_set()
            progress_window.configure(background=self.dark_green)
            
            # Progress display
            ttk.Label(progress_window, text="Fetching customer list...", style="Title.TLabel").pack(pady=(20, 10))
            
            # Progress bar
            progress_var = tk.DoubleVar()
            progress_bar = ttk.Progressbar(progress_window, variable=progress_var, length=500, mode='determinate')
            progress_bar.pack(pady=10, padx=20)
            
            # Status label
            status_var = tk.StringVar(value="Connecting to wiki...")
            status_label = ttk.Label(progress_window, textvariable=status_var, wraplength=550)
            status_label.pack(pady=10)
            
            # Cancel button
            self.import_cancelled = False
            cancel_button = ttk.Button(
                progress_window, 
                text="Cancel Import", 
                command=lambda: setattr(self, 'import_cancelled', True)
            )
            cancel_button.pack(pady=10)
            
            # Update UI
            progress_window.update()
            
            # Get the customer category page
            status_var.set("Fetching customer list from category page...")
            progress_window.update()
            
            url = "https://schedule-1.fandom.com/wiki/Category:Customers"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find all customer links - get actual customer links, not the category page
            customer_links = []
            category_members = soup.select('.category-page__member-link')
            
            for link in category_members:
                if link.has_attr('href') and "Category:" not in link['href'] and "Template:" not in link['href']:
                    customer_links.append("https://schedule-1.fandom.com" + link['href'])
            
            if not customer_links:
                progress_window.destroy()
                messagebox.showerror("Error", "No customer links found on the category page")
                return
            
            # Progress initialization
            total_customers = len(customer_links)
            new_customers = []
            
            # Ask if user wants to replace or append data
            if self.customer_data.get("customers", []):
                if messagebox.askyesno("Import Options", "Do you want to replace the existing customer database? Click 'No' to append new customers."):
                    self.customer_data["customers"] = []
            
            # Process each customer
            for i, link in enumerate(customer_links):
                if self.import_cancelled:
                    break
                
                try:
                    # Update progress
                    progress_var.set((i / total_customers) * 100)
                    customer_name = link.split('/')[-1].replace('_', ' ')
                    status_var.set(f"Processing {i+1} of {total_customers}: {customer_name}")
                    progress_window.update()
                    
                    # Request the customer page
                    response = requests.get(link, headers=headers)
                    response.raise_for_status()
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Extract customer name from title
                    title = soup.find('title')
                    name = title.text.split('|')[0].strip() if title else customer_name
                    
                    # Skip if this is a category page, template, or redirection
                    if ("Category:" in name or "Template:" in name or 
                        soup.find('div', class_='mw-redirectedfrom')):
                        status_var.set(f"Skipping {name} - not a customer page")
                        progress_window.update()
                        continue
                    
                    # Check if customer already exists - skip if it does
                    if any(c.get("name") == name for c in self.customer_data.get("customers", [])):
                        status_var.set(f"Skipping {name} - already in database")
                        progress_window.update()
                        continue
                    
                    # Try all extraction methods with debug output for each customer
                    customer_data = self._extract_customer_data_comprehensive(soup, name, link)
                    
                    # Add to the new customers list if we got any meaningful data
                    if (customer_data["region"] or customer_data["standards"] or 
                        customer_data["favorite_effects"] or customer_data["residency"] or 
                        customer_data["work"]):
                        new_customers.append(customer_data)
                        status_var.set(f"Added {name} with {len(customer_data['favorite_effects'])} effects")
                    else:
                        status_var.set(f"Skipping {name} - no data found")
                    progress_window.update()
                    
                except Exception as e:
                    status_var.set(f"Error processing {link}: {str(e)}")
                    progress_window.update()
                    import traceback
                    traceback.print_exc()
            
            # Close progress window
            progress_window.destroy()
            
            if self.import_cancelled:
                messagebox.showinfo("Import Cancelled", "Customer import cancelled. Some customers may have been imported.")
            else:
                # Add all new customers
                self.customer_data.setdefault("customers", []).extend(new_customers)
                
                # Save and refresh
                self.save_customer_data()
                self.refresh_customer_list()
                
                messagebox.showinfo("Import Complete", f"Successfully imported {len(new_customers)} customers")
                self.update_status(f"Imported {len(new_customers)} customers from wiki")
            
        except Exception as e:
            # Close progress window if it exists
            try:
                progress_window.destroy()
            except:
                pass
                
            messagebox.showerror("Import Error", f"An error occurred during import: {str(e)}")
            self.update_status("Customer import failed")
            import traceback
            traceback.print_exc()

    def _extract_customer_data_comprehensive(self, soup, name, url):
        """A comprehensive extraction method that tries multiple approaches to extract customer data"""
        customer_data = {
            "name": name,
            "region": "",
            "standards": "",
            "favorite_effects": [],
            "relations": [],
            "residency": "",
            "work": "",
            "notes": f"Imported from {url} on {datetime.datetime.now().strftime('%Y-%m-%d')}"
        }
        
        print(f"\n--- EXTRACTING DATA FOR {name} ---")
        
        # Try to find the article content
        article = soup.find('article', class_='WikiaArticle') or soup.find('div', class_='mw-parser-output')
        if not article:
            print(f"Warning: Could not find article content for {name}")
            # Use whole page if article section not found
            article = soup
        
        # APPROACH 1: Look for infobox-style data in tables
        try:
            # Modern wikis often use tables for infoboxes
            print("Trying extraction from tables...")
            tables = article.find_all('table')
            for table in tables:
                rows = table.find_all('tr')
                for row in rows:
                    # Try to find header and value cells
                    header_cell = row.find('th')
                    value_cell = row.find('td')
                    
                    if header_cell and value_cell:
                        header_text = header_cell.get_text().strip().lower()
                        value_text = value_cell.get_text().strip()
                        
                        print(f"Found table row: {header_text} = {value_text}")
                        
                        if "region" in header_text:
                            customer_data["region"] = value_text
                        elif "standard" in header_text:
                            if "low" in value_text.lower():
                                customer_data["standards"] = "Low"
                            elif "moderate" in value_text.lower() or "medium" in value_text.lower():
                                customer_data["standards"] = "Moderate"
                            elif "high" in value_text.lower():
                                customer_data["standards"] = "High"
                        elif "effect" in header_text and ("favorite" in header_text or "favourite" in header_text):
                            effects = self._process_effects_list(value_text)
                            customer_data["favorite_effects"] = effects
                        elif "relation" in header_text:
                            relations = self._process_relations_list(value_text)
                            customer_data["relations"] = relations
        except Exception as e:
            print(f"Error in table extraction: {e}")
        
        # APPROACH 2: Look for <div> based infoboxes (common in older Fandom wikis)
        try:
            print("Trying extraction from div-based infoboxes...")
            infobox = article.find('div', class_='portable-infobox') or article.find('aside', class_='portable-infobox')
            if (infobox):
                # Extract from portable infobox (modern)
                for item in infobox.find_all('div', class_='pi-item'):
                    label = item.find('h3', class_='pi-data-label')
                    value = item.find('div', class_='pi-data-value')
                    
                    if (label and value):
                        label_text = label.get_text().strip().lower()
                        value_text = value.get_text().strip()
                        
                        print(f"Found infobox item: {label_text} = {value_text}")
                        
                        if "region" in label_text:
                            customer_data["region"] = value_text
                        elif "standard" in label_text:
                            if "low" in value_text.lower():
                                customer_data["standards"] = "Low"
                            elif "moderate" in value_text.lower() or "medium" in value_text.lower():
                                customer_data["standards"] = "Moderate"
                            elif "high" in value_text.lower():
                                customer_data["standards"] = "High"
                        elif "effect" in label_text and ("favorite" in label_text or "favourite" in label_text):
                            effects = self._process_effects_list(value_text)
                            customer_data["favorite_effects"] = effects
                        elif "relation" in label_text:
                            relations = self._process_relations_list(value_text)
                            customer_data["relations"] = relations
            
            # Try older style div infoboxes
            div_labels = article.find_all('div', class_='label')
            for label in div_labels:
                label_text = label.get_text().strip().lower()
                value_div = label.find_next_sibling('div')
                
                if value_div:
                    value_text = value_div.get_text().strip()
                    print(f"Found div label: {label_text} = {value_text}")
                    
                    if "region" in label_text:
                        customer_data["region"] = value_text
                    elif "standard" in label_text:
                        if "low" in value_text.lower():
                            customer_data["standards"] = "Low"
                        elif "moderate" in value_text.lower() or "medium" in value_text.lower():
                            customer_data["standards"] = "Moderate"
                        elif "high" in value_text.lower():
                            customer_data["standards"] = "High"
                    elif "effect" in label_text and ("favorite" in label_text or "favourite" in label_text):
                        # Check if it's a list
                        list_items = value_div.find_all('li')
                        if list_items:
                            effects = [li.get_text().strip() for li in list_items]
                            effects = self._process_effects_list(", ".join(effects))
                        else:
                            effects = self._process_effects_list(value_text)
                        customer_data["favorite_effects"] = effects
                    elif "relation" in label_text:
                        # Check if it's a list
                        list_items = value_div.find_all('li')
                        if list_items:
                            relations = [li.get_text().strip() for li in list_items]
                            relations = self._process_relations_list(", ".join(relations))
                        else:
                            relations = self._process_relations_list(value_text)
                        customer_data["relations"] = relations
        except Exception as e:
            print(f"Error in div infobox extraction: {e}")
        
        # APPROACH 3: Look for data in bold text followed by regular text
        try:
            print("Trying extraction from bold text patterns...")
            # Find all bold elements
            bold_elements = article.find_all(['b', 'strong'])
            for bold in bold_elements:
                bold_text = bold.get_text().strip().lower()
                next_element = bold.next_sibling
                if next_element and isinstance(next_element, str):
                    value_text = next_element.strip()
                    if value_text.startswith(':'):
                        value_text = value_text[1:].strip()
                    
                    print(f"Found bold pattern: {bold_text} => {value_text}")
                    
                    if "region" in bold_text:
                        customer_data["region"] = value_text
                    elif "standard" in bold_text:
                        if "low" in value_text.lower():
                            customer_data["standards"] = "Low"
                        elif "moderate" in value_text.lower() or "medium" in value_text.lower():
                            customer_data["standards"] = "Moderate"
                        elif "high" in value_text.lower():
                            customer_data["standards"] = "High"
                    elif "effect" in bold_text and ("favorite" in bold_text or "favourite" in bold_text):
                        effects = self._process_effects_list(value_text)
                        customer_data["favorite_effects"] = effects
                    elif "relation" in bold_text:
                        relations = self._process_relations_list(value_text)
                        customer_data["relations"] = relations
        except Exception as e:
            print(f"Error in bold text extraction: {e}")
        
        # APPROACH 4: Try section-based extraction for residency and work
        try:
            print("Trying section-based extraction...")
            headers = article.find_all(['h2', 'h3', 'h4'])
            for header in headers:
                header_text = header.get_text().strip().lower()
                print(f"Found section header: {header_text}")
                
                if "residency" in header_text:
                    # Get the next paragraph
                    next_p = header.find_next('p')
                    if next_p:
                        customer_data["residency"] = next_p.get_text().strip()
                        print(f"Found residency text: {customer_data['residency'][:30]}...")
                elif "work" in header_text:
                    # Get the next paragraph
                    next_p = header.find_next('p')
                    if next_p:
                        customer_data["work"] = next_p.get_text().strip()
                        print(f"Found work text: {customer_data['work'][:30]}...")
        except Exception as e:
            print(f"Error in section extraction: {e}")
        
        # APPROACH 5: Look for template-defined data
        try:
            print("Trying template data extraction...")
            # Check for data in specially formatted areas, which might be from templates
            data_blocks = article.find_all('div', class_='data')
            for block in data_blocks:
                # Look for header inside or before the block
                header = block.find_previous_sibling('div', class_='header') or block.find('div', class_='header')
                if header:
                    header_text = header.get_text().strip().lower()
                    value_text = block.get_text().strip()
                    
                    print(f"Found data block: {header_text} = {value_text}")
                    
                    if "region" in header_text:
                        customer_data["region"] = value_text
                    elif "standard" in header_text:
                        if "low" in value_text.lower():
                            customer_data["standards"] = "Low"
                        elif "moderate" in value_text.lower() or "medium" in value_text.lower():
                            customer_data["standards"] = "Moderate"
                        elif "high" in value_text.lower():
                            customer_data["standards"] = "High"
                    elif "effect" in header_text and ("favorite" in header_text or "favourite" in header_text):
                        effects = self._process_effects_list(value_text)
                        customer_data["favorite_effects"] = effects
                    elif "relation" in header_text:
                        relations = self._process_relations_list(value_text)
                        customer_data["relations"] = relations
        except Exception as e:
            print(f"Error in template data extraction: {e}")
        
        # APPROACH 6: Direct search for text patterns in the entire content
        try:
            print("Trying direct text pattern search...")
            html_content = str(article)
            
            # Look for region data
            region_match = re.search(r'[Rr]egion\s*[:-]\s*([^<>\n,]+)', html_content)
            if region_match and not customer_data["region"]:
                customer_data["region"] = region_match.group(1).strip()
                print(f"Found region via regex: {customer_data['region']}")
            
            # Look for standards data
            standards_match = re.search(r'[Ss]tandards?\s*[:-]\s*([^<>\n,]+)', html_content)
            if standards_match and not customer_data["standards"]:
                standards_text = standards_match.group(1).strip().lower()
                if "low" in standards_text:
                    customer_data["standards"] = "Low"
                elif "moderate" in standards_text or "medium" in standards_text:
                    customer_data["standards"] = "Moderate"
                elif "high" in standards_text:
                    customer_data["standards"] = "High"
                print(f"Found standards via regex: {customer_data['standards']}")
            
            # Look for effects data
            effects_match = re.search(r'[Ff]av(?:ou|o)rite [Ee]ffects?\s*[:-]\s*([^<>]+?)(?:<|$)', html_content)
            if effects_match and not customer_data["favorite_effects"]:
                effects_text = effects_match.group(1).strip()
                effects = self._process_effects_list(effects_text)
                customer_data["favorite_effects"] = effects
                print(f"Found effects via regex: {customer_data['favorite_effects']}")
            
            # Look for relations data
            relations_match = re.search(r'[Rr]elations?\s*[:-]\s*([^<>]+?)(?:<|$)', html_content)
            if relations_match and not customer_data["relations"]:
                relations_text = relations_match.group(1).strip()
                relations = self._process_relations_list(relations_text)
                customer_data["relations"] = relations
                print(f"Found relations via regex: {customer_data['relations']}")
            
            # Look for residency data
            if not customer_data["residency"]:
                residency_match = re.search(r'(?:<h[23]>.*?[Rr]esidency.*?</h[23]>)(.*?)(?:<h[23]>|$)', html_content, re.DOTALL)
                if residency_match:
                    residency_html = residency_match.group(1).strip()
                    # Extract text from paragraph if present
                    paragraph_match = re.search(r'<p>(.*?)</p>', residency_html, re.DOTALL)
                    if paragraph_match:
                        residency_text = paragraph_match.group(1).strip()
                        # Remove HTML tags
                        residency_text = re.sub(r'<[^>]+>', '', residency_text)
                        customer_data["residency"] = residency_text
                        print(f"Found residency via regex: {customer_data['residency'][:30]}...")
            
            # Look for work data
            if not customer_data["work"]:
                work_match = re.search(r'(?:<h[23]>.*?[Ww]ork.*?</h[23]>)(.*?)(?:<h[23]>|$)', html_content, re.DOTALL)
                if work_match:
                    work_html = work_match.group(1).strip()
                    # Extract text from paragraph if present
                    paragraph_match = re.search(r'<p>(.*?)</p>', work_html, re.DOTALL)
                    if paragraph_match:
                        work_text = paragraph_match.group(1).strip()
                        # Remove HTML tags
                        work_text = re.sub(r'<[^>]+>', '', work_text)
                        customer_data["work"] = work_text
                        print(f"Found work via regex: {customer_data['work'][:30]}...")
        except Exception as e:
            print(f"Error in direct text search: {e}")
        
        # Set default values for any empty fields
        if not customer_data["region"]:
            customer_data["region"] = "Not Available"
            
        if not customer_data["standards"]:
            customer_data["standards"] = "Not Available"
            
        if not customer_data["favorite_effects"]:
            customer_data["favorite_effects"] = ["Not Available"]
            
        if not customer_data["relations"]:
            customer_data["relations"] = ["Not Available"]
            
        if not customer_data["residency"]:
            customer_data["residency"] = "Not Available"
            
        if not customer_data["work"]:
            customer_data["work"] = "Not Available"
        
        # Print summary of what we found
        print("\nExtraction summary:")
        print(f"Region: {customer_data['region']}")
        print(f"Standards: {customer_data['standards']}")
        print(f"Favorite Effects: {customer_data['favorite_effects']}")
        print(f"Relations: {customer_data['relations']}")
        print(f"Residency: {customer_data['residency'][:30]}..." if len(customer_data['residency']) > 30 else f"Residency: {customer_data['residency']}")
        print(f"Work: {customer_data['work'][:30]}..." if len(customer_data['work']) > 30 else f"Work: {customer_data['work']}")
        
        return customer_data
        
    def _process_effects_list(self, text):
        """Process a list of effects, handling cases where they're squished together"""
        if not text:
            return []
            
        # List of all known effects for pattern matching
        known_effects = [
            "Calming", "Sedating", "Refreshing", "Euphoric", "Energizing", 
            "Disorienting", "Foggy", "Glowing", "Balding", "Athletic", 
            "Focused", "Thought-Provoking", "Sneaky", "Munchies", 
            "Smelly", "Spicy", "Toxic", "Slippery", "Calorie-Dense",
            "Shrinking", "Gingeritis", "Long Faced", "Bright-Eyed",
            "Seizure-Inducing", "Laxative", "Paranoia", "Tropic Thunder",
            "Schizophrenic", "Explosive", "Anti-Gravity", "Lethal",
            "Jennerising", "Electrifying"
        ]
        
        # First try splitting by commas and other separators
        effects = []
        for part in re.split(r'[,;/]+', text):
            part = part.strip()
            if part:
                effects.append(part)
        
        # Check if we have any squished-together effects
        new_effects = []
        for effect in effects:
            # If the effect contains known effect names without spaces between them
            if any(e in effect for e in known_effects) and len(effect) > 20:
                # Create a regex pattern that looks for all known effects
                pattern = '|'.join(known_effects)
                pattern = f'({pattern})'
                
                # Find all effect names in the string
                found_effects = re.findall(pattern, effect)
                if found_effects:
                    new_effects.extend(found_effects)
                else:
                    new_effects.append(effect)
            else:
                new_effects.append(effect)
        
        return new_effects if new_effects else []
    
    def _process_relations_list(self, text):
        """Process a list of relations, handling cases where they're squished together"""
        if not text:
            return []
        
        # First try splitting by commas and other separators
        relations = []
        for part in re.split(r'[,;/]+', text):
            part = part.strip()
            if part:
                relations.append(part)
        
        # Check if we have any squished-together names
        new_relations = []
        for relation in relations:
            # If the relation is unusually long without spaces, try to split it
            if relation and len(relation) > 20:
                # Split by capital letter preceded by lowercase (e.g., "JohnSmith" -> ["John", "Smith"])
                split_relations = re.findall(r'[A-Z][^A-Z]*', relation)
                if split_relations:
                    new_relations.extend(split_relations)
                else:
                    new_relations.append(relation)
            else:
                new_relations.append(relation)
        
        return new_relations if new_relations else []

    def sort_customers_by_column(self, column):
        """Sort the customer list by the selected column"""
        items = [(self.customer_tree.set(child, column), child) for child in self.customer_tree.get_children('')]
        
        # Determine sort direction (toggle current direction)
        reverse = False
        if self.customer_sort_column == column and not self.customer_sort_reverse:
            reverse = True
        
        # Update sort state
        self.customer_sort_column = column
        self.customer_sort_reverse = reverse
        
        # Sort the items
        items.sort(reverse=reverse)
        
        # Move items in the sorted order
        for index, (_, child) in enumerate(items):
            self.customer_tree.move(child, '', index)
            
        # Update headings to show sort direction
        for col in ["Name", "Region", "Standards", "Favorite Effects"]:
            if col == column:
                direction = " ▼" if reverse else " ▲"
                self.customer_tree.heading(col, text=f"{col}{direction}")
            else:
                self.customer_tree.heading(col, text=col)
        
        # Update status
        direction_text = "descending" if reverse else "ascending"
        self.update_status(f"Sorted customers by {column} ({direction_text})")
    
    def load_dealer_data(self):
        """Load dealer data from file and update the UI if needed.
        This method is called after dealer data is updated in the background."""
        from src.dealer_data import load_dealer_data
        
        try:
            self.dealer_data = load_dealer_data()
            
            # If there's a dealer tab, we'd update it here
            # This will be implemented when the dealer management tab is added
            
            # Update status with count of loaded dealers
            dealer_count = len(self.dealer_data.get("dealers", []))
            self.update_status(f"Dealer data updated: {dealer_count} dealers loaded")
            
            return True
        except Exception as e:
            self.update_status(f"Error loading dealer data: {str(e)}")
            print(f"Error loading dealer data: {e}")
            return False


class FixedHeader(ttk.Frame):
    """A custom widget that combines a treeview with a fixed header.
    This enables the header to remain visible even when scrolling through a large dataset."""
    def __init__(self, parent, columns, show="headings", height=10, **kwargs):
        super().__init__(parent)
        
        # Configure grid layout
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        
        # Create the header treeview (fixed, no scrolling)
        self.header = ttk.Treeview(self, columns=columns, show=show, height=1)
        self.header.grid(row=0, column=0, sticky="ew")
        
        # Create container frame for the scrollable treeview
        self.tree_frame = ttk.Frame(self)
        self.tree_frame.grid(row=1, column=0, sticky="nsew")
        self.tree_frame.columnconfigure(0, weight=1)
        self.tree_frame.rowconfigure(0, weight=1)
        
        # Create the main treeview
        self.tree = ttk.Treeview(self.tree_frame, columns=columns, show=show, height=height, **kwargs)
        self.tree.grid(row=0, column=0, sticky="nsew")
        
        # Add vertical scrollbar to the main treeview
        self.vsb = ttk.Scrollbar(self.tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=self.vsb.set)
        self.vsb.grid(row=0, column=1, sticky="ns")
        
        # Add horizontal scrollbar
        self.hsb = ttk.Scrollbar(self, orient=tk.HORIZONTAL, command=self._scroll_both)
        self.tree.configure(xscrollcommand=self.hsb.set)
        self.header.configure(xscrollcommand=self.hsb.set)
        self.hsb.grid(row=2, column=0, sticky="ew")
        
        # Sync headers
        self._setup_headers(columns)
        
    def _scroll_both(self, *args):
        """Scroll both the header and the main treeview horizontally"""
        self.header.xview(*args)
        self.tree.xview(*args)
    
    def _setup_headers(self, columns):
        """Setup the headers to match the main treeview"""
        for col in columns:
            self.header.heading(col, text=col)
            self.header.column(col, width=100)
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100)
    
    def insert(self, *args, **kwargs):
        """Insert a row into the main treeview"""
        self.tree.insert(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        """Delete a row from the main treeview"""
        self.tree.delete(*args, **kwargs)
    
    def get_children(self, *args, **kwargs):
        """Get children of the main treeview"""
        return self.tree.get_children(*args, **kwargs)
    
    def selection(self, *args, **kwargs):
        """Get or set the selection of the main treeview"""
        return self.tree.selection(*args, **kwargs)
    
    def bind(self, *args, **kwargs):
        """Bind an event to the main treeview"""
        self.tree.bind(*args, **kwargs)
    
    def column(self, *args, **kwargs):
        """Configure a column of the main treeview"""
        self.tree.column(*args, **kwargs)
    
    def heading(self, *args, **kwargs):
        """Configure a heading of the main treeview"""
        self.tree.heading(*args, **kwargs)


if __name__ == "__main__":
    root = tk.Tk()
    app = ScheduleICalculatorApp(root)
    root.mainloop()