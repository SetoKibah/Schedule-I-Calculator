"""
Schedule I Data Analyzer
Analyzes testing data to suggest improvements to the calculator.
"""

import json
import os
import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from src.game_data import MARIJUANA_STRAINS, MIXERS, EFFECTS
from src.calculator import calculate_market_value, get_effects_from_mixers


class ScheduleIAnalyzerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Schedule I Data Analyzer")
        self.root.geometry("1000x800")
        
        # Data file path
        self.data_file = "testing_data.json"
        self.test_data = self.load_test_data()
        
        # Analysis results
        self.effect_discrepancies = {}
        self.value_discrepancies = {}
        self.pattern_suggestions = []
        
        self.setup_ui()
        
    def load_test_data(self):
        """Load testing data from file"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                messagebox.showerror("Error", f"Could not parse {self.data_file}. File may be corrupted.")
                return {"combinations": []}
        else:
            messagebox.showinfo("Info", f"No testing data file found at {self.data_file}. Please add test cases first.")
            return {"combinations": []}
    
    def setup_ui(self):
        """Set up the user interface"""
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Add tabs
        self.overview_frame = ttk.Frame(notebook)
        self.effect_analysis_frame = ttk.Frame(notebook)
        self.value_analysis_frame = ttk.Frame(notebook) 
        self.code_suggestions_frame = ttk.Frame(notebook)
        
        notebook.add(self.overview_frame, text="Overview")
        notebook.add(self.effect_analysis_frame, text="Effect Analysis")
        notebook.add(self.value_analysis_frame, text="Value Analysis")
        notebook.add(self.code_suggestions_frame, text="Code Suggestions")
        
        self.setup_overview_tab()
        self.setup_effect_analysis_tab()
        self.setup_value_analysis_tab()
        self.setup_code_suggestions_tab()
        
        # Run analysis on startup if we have data
        if self.test_data["combinations"]:
            self.run_analysis()
    
    def setup_overview_tab(self):
        """Set up the Overview tab"""
        frame = self.overview_frame
        
        # Top section - Summary stats
        stats_frame = ttk.LabelFrame(frame, text="Dataset Summary")
        stats_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.summary_text = tk.Text(stats_frame, height=5, width=80)
        self.summary_text.pack(padx=10, pady=10, fill=tk.X)
        self.summary_text.config(state=tk.DISABLED)
        
        # Middle section - Controls
        control_frame = ttk.Frame(frame)
        control_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(control_frame, text="Reload Data", command=self.reload_data).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Run Analysis", command=self.run_analysis).pack(side=tk.LEFT, padx=5)
        
        # Bottom section - Charts
        charts_frame = ttk.LabelFrame(frame, text="Data Visualization")
        charts_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.fig = plt.Figure(figsize=(10, 6))
        self.canvas = FigureCanvasTkAgg(self.fig, charts_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    def setup_effect_analysis_tab(self):
        """Set up the Effect Analysis tab"""
        frame = self.effect_analysis_frame
        
        # Top control area
        control_frame = ttk.Frame(frame)
        control_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(control_frame, text="Filter by Base:").pack(side=tk.LEFT, padx=5)
        self.effect_base_var = tk.StringVar(value="All")
        self.effect_base_combo = ttk.Combobox(control_frame, textvariable=self.effect_base_var, width=15)
        bases = ["All"] + list(MARIJUANA_STRAINS.keys())
        self.effect_base_combo['values'] = bases
        self.effect_base_combo.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(control_frame, text="Filter by Mixer:").pack(side=tk.LEFT, padx=5)
        self.effect_mixer_var = tk.StringVar(value="All")
        self.effect_mixer_combo = ttk.Combobox(control_frame, textvariable=self.effect_mixer_var, width=15)
        mixers = ["All"] + list(MIXERS.keys())
        self.effect_mixer_combo['values'] = mixers
        self.effect_mixer_combo.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(control_frame, text="Apply Filter", command=self.update_effect_analysis).pack(side=tk.LEFT, padx=20)
        
        # Table of effect discrepancies
        ttk.Label(frame, text="Effect Prediction Discrepancies:").pack(anchor=tk.W, padx=10, pady=5)
        
        table_frame = ttk.Frame(frame)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        columns = ("Base", "Mixer", "Predicted Effects", "Actual Effects", "Status")
        self.effect_tree = ttk.Treeview(table_frame, columns=columns, show="headings")
        
        # Configure columns
        for col in columns:
            self.effect_tree.heading(col, text=col)
            if col in ("Predicted Effects", "Actual Effects"):
                self.effect_tree.column(col, width=200)
            elif col == "Status":
                self.effect_tree.column(col, width=100)
            else:
                self.effect_tree.column(col, width=120)
        
        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.effect_tree.yview)
        self.effect_tree.configure(yscroll=scrollbar.set)
        
        self.effect_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Pattern detection area
        pattern_frame = ttk.LabelFrame(frame, text="Detected Effect Patterns")
        pattern_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.effect_pattern_text = tk.Text(pattern_frame, height=6, width=80)
        self.effect_pattern_text.pack(padx=10, pady=10, fill=tk.X)
        self.effect_pattern_text.config(state=tk.DISABLED)
    
    def setup_value_analysis_tab(self):
        """Set up the Value Analysis tab"""
        frame = self.value_analysis_frame
        
        # Top control area
        control_frame = ttk.Frame(frame)
        control_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(control_frame, text="Filter by Base:").pack(side=tk.LEFT, padx=5)
        self.value_base_var = tk.StringVar(value="All")
        self.value_base_combo = ttk.Combobox(control_frame, textvariable=self.value_base_var, width=15)
        bases = ["All"] + list(MARIJUANA_STRAINS.keys())
        self.value_base_combo['values'] = bases
        self.value_base_combo.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(control_frame, text="Apply Filter", command=self.update_value_analysis).pack(side=tk.LEFT, padx=20)
        
        # Table of value discrepancies
        ttk.Label(frame, text="Market Value Prediction Discrepancies:").pack(anchor=tk.W, padx=10, pady=5)
        
        table_frame = ttk.Frame(frame)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        columns = ("Base", "Mixer", "Predicted Value", "Actual Value", "Difference", "% Error")
        self.value_tree = ttk.Treeview(table_frame, columns=columns, show="headings")
        
        # Configure columns
        for col in columns:
            self.value_tree.heading(col, text=col)
            self.value_tree.column(col, width=120)
        
        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.value_tree.yview)
        self.value_tree.configure(yscroll=scrollbar.set)
        
        self.value_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Scatter plot of predicted vs actual
        plot_frame = ttk.LabelFrame(frame, text="Prediction Accuracy")
        plot_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.value_fig = plt.Figure(figsize=(8, 4))
        self.value_canvas = FigureCanvasTkAgg(self.value_fig, plot_frame)
        self.value_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    def setup_code_suggestions_tab(self):
        """Set up the Code Suggestions tab"""
        frame = self.code_suggestions_frame
        
        # Control area
        control_frame = ttk.Frame(frame)
        control_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(control_frame, text="Generate Code Suggestions", command=self.generate_code_suggestions).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Export Suggestions", command=self.export_suggestions).pack(side=tk.LEFT, padx=5)
        
        # Suggestions text area
        suggestions_frame = ttk.LabelFrame(frame, text="Suggested Code Changes")
        suggestions_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.suggestions_text = tk.Text(suggestions_frame, wrap=tk.WORD, width=80)
        self.suggestions_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    def reload_data(self):
        """Reload test data from file"""
        self.test_data = self.load_test_data()
        messagebox.showinfo("Info", "Data reloaded successfully!")
        self.run_analysis()
    
    def run_analysis(self):
        """Run the analysis on the loaded test data"""
        if not self.test_data["combinations"]:
            messagebox.showinfo("Info", "No test data available for analysis. Please add test cases first.")
            return
        
        # Update summary statistics
        self.update_summary()
        
        # Analyze effect discrepancies
        self.analyze_effects()
        self.update_effect_analysis()
        
        # Analyze value discrepancies  
        self.analyze_values()
        self.update_value_analysis()
        
        # Generate visualization
        self.create_visualizations()
        
        # Generate code suggestions
        self.generate_code_suggestions()
        
        messagebox.showinfo("Success", "Analysis completed successfully!")
    
    def update_summary(self):
        """Update the summary statistics"""
        combinations = self.test_data["combinations"]
        
        # Calculate statistics
        total_cases = len(combinations)
        
        if total_cases == 0:
            return
            
        bases_used = set(case["base"] for case in combinations)
        mixers_used = set(case["mixer"] for case in combinations)
        
        effect_errors = sum(1 for case in combinations 
                           if case["actual_effects"] and set(case["predicted_effects"]) != set(case["actual_effects"]))
        
        value_errors = sum(1 for case in combinations 
                          if case["actual_value"] and case["predicted_value"] != case["actual_value"])
        
        effect_accuracy = 100 * (total_cases - effect_errors) / total_cases if total_cases > 0 else 0
        value_accuracy = 100 * (total_cases - value_errors) / total_cases if total_cases > 0 else 0
        
        # Update summary text
        self.summary_text.config(state=tk.NORMAL)
        self.summary_text.delete(1.0, tk.END)
        
        self.summary_text.insert(tk.END, f"Total Test Cases: {total_cases}\n")
        self.summary_text.insert(tk.END, f"Bases Tested: {len(bases_used)} ({', '.join(bases_used)})\n")
        self.summary_text.insert(tk.END, f"Mixers Tested: {len(mixers_used)} ({', '.join(list(mixers_used)[:5])}{'...' if len(mixers_used) > 5 else ''})\n")
        self.summary_text.insert(tk.END, f"Effect Prediction Accuracy: {effect_accuracy:.1f}%\n")
        self.summary_text.insert(tk.END, f"Value Prediction Accuracy: {value_accuracy:.1f}%\n")
        
        self.summary_text.config(state=tk.DISABLED)
    
    def analyze_effects(self):
        """Analyze effect prediction discrepancies"""
        self.effect_discrepancies = {}
        
        for case in self.test_data["combinations"]:
            if not case["actual_effects"]:
                continue
                
            base = case["base"]
            mixer = case["mixer"]
            predicted = set(case["predicted_effects"])
            actual = set(case["actual_effects"])
            
            if predicted != actual:
                missing = actual - predicted
                extra = predicted - actual
                
                key = (base, mixer)
                self.effect_discrepancies[key] = {
                    "base": base,
                    "mixer": mixer,
                    "predicted": case["predicted_effects"],
                    "actual": case["actual_effects"],
                    "missing": list(missing),
                    "extra": list(extra)
                }
        
        # Detect patterns in effect discrepancies
        self.detect_effect_patterns()
    
    def update_effect_analysis(self):
        """Update the effect analysis table based on filters"""
        # Clear existing items
        for item in self.effect_tree.get_children():
            self.effect_tree.delete(item)
        
        # Apply filters
        base_filter = self.effect_base_var.get()
        mixer_filter = self.effect_mixer_var.get()
        
        for key, discrepancy in self.effect_discrepancies.items():
            base, mixer = key
            
            # Apply filters
            if (base_filter != "All" and base != base_filter) or (mixer_filter != "All" and mixer != mixer_filter):
                continue
            
            # Determine status
            if discrepancy["extra"] and discrepancy["missing"]:
                status = "Different"
                tag = "different"
            elif discrepancy["extra"]:
                status = "Extra Effects"
                tag = "extra"
            elif discrepancy["missing"]:
                status = "Missing Effects"
                tag = "missing"
            else:
                status = "OK"
                tag = "ok"
            
            # Insert into tree
            self.effect_tree.insert("", tk.END, values=(
                base, 
                mixer, 
                ", ".join(discrepancy["predicted"]), 
                ", ".join(discrepancy["actual"]),
                status
            ), tags=(tag,))
        
        # Configure tags
        self.effect_tree.tag_configure("different", background="#ffcccc")
        self.effect_tree.tag_configure("extra", background="#ffffcc")
        self.effect_tree.tag_configure("missing", background="#ccffcc")
    
    def detect_effect_patterns(self):
        """Detect patterns in effect discrepancies"""
        # Initialize pattern storage
        self.effect_patterns = []
        
        # Group by base product
        base_patterns = {}
        for key, discrepancy in self.effect_discrepancies.items():
            base, mixer = key
            if base not in base_patterns:
                base_patterns[base] = []
            base_patterns[base].append(discrepancy)
        
        # Look for consistent patterns within each base
        for base, discrepancies in base_patterns.items():
            # Count occurrences of each missing and extra effect
            missing_counts = {}
            extra_counts = {}
            
            for disc in discrepancies:
                for effect in disc["missing"]:
                    missing_counts[effect] = missing_counts.get(effect, 0) + 1
                for effect in disc["extra"]:
                    extra_counts[effect] = extra_counts.get(effect, 0) + 1
            
            # Check for consistent patterns (appearing in majority of cases)
            threshold = len(discrepancies) / 2  # At least half of the cases
            
            for effect, count in missing_counts.items():
                if count >= threshold:
                    self.effect_patterns.append({
                        "base": base,
                        "mixer": "Any",
                        "type": "missing",
                        "effect": effect,
                        "frequency": f"{count}/{len(discrepancies)}"
                    })
            
            for effect, count in extra_counts.items():
                if count >= threshold:
                    self.effect_patterns.append({
                        "base": base,
                        "mixer": "Any",
                        "type": "extra",
                        "effect": effect,
                        "frequency": f"{count}/{len(discrepancies)}"
                    })
        
        # Look for specific mixer patterns
        mixer_patterns = {}
        for key, discrepancy in self.effect_discrepancies.items():
            base, mixer = key
            if mixer not in mixer_patterns:
                mixer_patterns[mixer] = []
            mixer_patterns[mixer].append(discrepancy)
        
        for mixer, discrepancies in mixer_patterns.items():
            # Similar logic as above, but for mixers
            missing_counts = {}
            extra_counts = {}
            
            for disc in discrepancies:
                for effect in disc["missing"]:
                    missing_counts[effect] = missing_counts.get(effect, 0) + 1
                for effect in disc["extra"]:
                    extra_counts[effect] = extra_counts.get(effect, 0) + 1
            
            threshold = len(discrepancies) / 2
            
            for effect, count in missing_counts.items():
                if count >= threshold:
                    self.effect_patterns.append({
                        "base": "Any",
                        "mixer": mixer,
                        "type": "missing",
                        "effect": effect,
                        "frequency": f"{count}/{len(discrepancies)}"
                    })
            
            for effect, count in extra_counts.items():
                if count >= threshold:
                    self.effect_patterns.append({
                        "base": "Any",
                        "mixer": mixer,
                        "type": "extra",
                        "effect": effect,
                        "frequency": f"{count}/{len(discrepancies)}"
                    })
        
        # Look for specific base+mixer combinations
        combination_patterns = {}
        for key, discrepancy in self.effect_discrepancies.items():
            if len(discrepancy["missing"]) == 1 and len(discrepancy["extra"]) == 1:
                base, mixer = key
                missing = discrepancy["missing"][0]
                extra = discrepancy["extra"][0]
                
                self.effect_patterns.append({
                    "base": base,
                    "mixer": mixer,
                    "type": "replacement",
                    "effect": f"{extra} -> {missing}",
                    "frequency": "1/1"
                })
        
        # Update the pattern text
        self.effect_pattern_text.config(state=tk.NORMAL)
        self.effect_pattern_text.delete(1.0, tk.END)
        
        if not self.effect_patterns:
            self.effect_pattern_text.insert(tk.END, "No consistent effect patterns detected.")
        else:
            for pattern in self.effect_patterns:
                if pattern["type"] == "missing":
                    self.effect_pattern_text.insert(tk.END, f"When using {pattern['base']} with {pattern['mixer']}, " 
                                                 f"effect '{pattern['effect']}' is missing from prediction ({pattern['frequency']} cases)\n")
                elif pattern["type"] == "extra":
                    self.effect_pattern_text.insert(tk.END, f"When using {pattern['base']} with {pattern['mixer']}, " 
                                                 f"effect '{pattern['effect']}' is incorrectly predicted ({pattern['frequency']} cases)\n")
                elif pattern["type"] == "replacement":
                    self.effect_pattern_text.insert(tk.END, f"When using {pattern['base']} with {pattern['mixer']}, " 
                                                 f"'{pattern['effect']}' replacement pattern detected\n")
        
        self.effect_pattern_text.config(state=tk.DISABLED)
    
    def analyze_values(self):
        """Analyze market value prediction discrepancies"""
        self.value_discrepancies = {}
        
        for case in self.test_data["combinations"]:
            if not case["actual_value"]:
                continue
                
            base = case["base"]
            mixer = case["mixer"]
            predicted = case["predicted_value"]
            actual = case["actual_value"]
            
            if predicted != actual:
                difference = actual - predicted
                pct_error = (difference / actual) * 100 if actual != 0 else float('inf')
                
                key = (base, mixer)
                self.value_discrepancies[key] = {
                    "base": base,
                    "mixer": mixer,
                    "predicted": predicted,
                    "actual": actual,
                    "difference": difference,
                    "pct_error": pct_error
                }
    
    def update_value_analysis(self):
        """Update the value analysis table based on filters"""
        # Clear existing items
        for item in self.value_tree.get_children():
            self.value_tree.delete(item)
        
        # Apply filters
        base_filter = self.value_base_var.get()
        
        for key, discrepancy in self.value_discrepancies.items():
            base, mixer = key
            
            # Apply filter
            if base_filter != "All" and base != base_filter:
                continue
            
            # Insert into tree
            self.value_tree.insert("", tk.END, values=(
                base, 
                mixer, 
                f"${discrepancy['predicted']}", 
                f"${discrepancy['actual']}",
                f"${discrepancy['difference']}",
                f"{discrepancy['pct_error']:.1f}%"
            ))
        
        # Create scatter plot
        self.create_value_chart()
    
    def create_value_chart(self):
        """Create the value prediction accuracy chart"""
        # Get data for plotting
        predicted = []
        actual = []
        bases = []
        
        for key, discrepancy in self.value_discrepancies.items():
            base, mixer = key
            
            # Apply filter
            if self.value_base_var.get() != "All" and base != self.value_base_var.get():
                continue
                
            predicted.append(discrepancy["predicted"])
            actual.append(discrepancy["actual"])
            bases.append(base)
        
        # Create plot
        self.value_fig.clear()
        ax = self.value_fig.add_subplot(111)
        
        # Plot scatter with different colors for different bases
        unique_bases = list(set(bases))
        colors = plt.cm.tab10(np.linspace(0, 1, len(unique_bases)))
        
        for i, base in enumerate(unique_bases):
            base_indices = [j for j, b in enumerate(bases) if b == base]
            ax.scatter([predicted[j] for j in base_indices], 
                       [actual[j] for j in base_indices], 
                       color=colors[i], label=base, alpha=0.7)
        
        # Add identity line (perfect prediction)
        max_val = max(max(predicted), max(actual)) if predicted and actual else 100
        ax.plot([0, max_val], [0, max_val], 'k--', alpha=0.5)
        
        # Add labels
        ax.set_xlabel("Predicted Value ($)")
        ax.set_ylabel("Actual Value ($)")
        ax.set_title("Market Value Prediction Accuracy")
        ax.grid(True, alpha=0.3)
        
        if len(unique_bases) > 1:
            ax.legend()
        
        self.value_fig.tight_layout()
        self.value_canvas.draw()
    
    def create_visualizations(self):
        """Create overview visualizations"""
        self.fig.clear()
        
        # Create subplots
        ax1 = self.fig.add_subplot(121)
        ax2 = self.fig.add_subplot(122)
        
        # First chart: Base product distribution
        base_counts = {}
        for case in self.test_data["combinations"]:
            base = case["base"]
            base_counts[base] = base_counts.get(base, 0) + 1
        
        bases = list(base_counts.keys())
        counts = list(base_counts.values())
        
        ax1.barh(bases, counts)
        ax1.set_xlabel("Number of Test Cases")
        ax1.set_title("Test Cases by Base Product")
        
        # Second chart: Effect prediction accuracy by base
        effect_accuracy = {}
        for case in self.test_data["combinations"]:
            if not case["actual_effects"]:
                continue
                
            base = case["base"]
            
            if base not in effect_accuracy:
                effect_accuracy[base] = {"correct": 0, "total": 0}
            
            effect_accuracy[base]["total"] += 1
            if set(case["predicted_effects"]) == set(case["actual_effects"]):
                effect_accuracy[base]["correct"] += 1
        
        bases = list(effect_accuracy.keys())
        accuracy = [100 * effect_accuracy[base]["correct"] / effect_accuracy[base]["total"] 
                   if effect_accuracy[base]["total"] > 0 else 0 for base in bases]
        
        ax2.barh(bases, accuracy, color='green')
        ax2.set_xlabel("Accuracy (%)")
        ax2.set_xlim(0, 100)
        ax2.set_title("Effect Prediction Accuracy")
        
        self.fig.tight_layout()
        self.canvas.draw()
    
    def generate_code_suggestions(self):
        """Generate code suggestions based on the analysis results"""
        self.pattern_suggestions = []
        
        # Clear suggestions text
        self.suggestions_text.delete(1.0, tk.END)
        
        # Check if we have enough data
        if not self.effect_discrepancies and not self.value_discrepancies:
            self.suggestions_text.insert(tk.END, "Not enough test data to generate meaningful suggestions.\n")
            self.suggestions_text.insert(tk.END, "Try adding more test cases with actual effects and values observed in-game.")
            return
        
        # 1. Effect replacement suggestions
        if hasattr(self, 'effect_patterns') and self.effect_patterns:
            self.suggestions_text.insert(tk.END, "=== Effect Prediction Improvements ===\n\n")
            
            for pattern in self.effect_patterns:
                if pattern["type"] == "replacement":
                    base = pattern["base"]
                    mixer = pattern["mixer"]
                    effect_parts = pattern["effect"].split(" -> ")
                    if len(effect_parts) == 2:
                        wrong_effect, correct_effect = effect_parts
                        
                        suggestion = {
                            "type": "effect_replacement",
                            "base": base,
                            "mixer": mixer,
                            "wrong_effect": wrong_effect,
                            "correct_effect": correct_effect,
                            "code": f'# Add to EFFECT_REPLACEMENTS in game_data.py\n'
                                  f'("{wrong_effect}", "{mixer}"): "{correct_effect}",'
                        }
                        
                        self.pattern_suggestions.append(suggestion)
                        
                        self.suggestions_text.insert(tk.END, f"SUGGESTION: When mixing {base} with {mixer},\n")
                        self.suggestions_text.insert(tk.END, f"'{wrong_effect}' should be replaced with '{correct_effect}'.\n\n")
                        self.suggestions_text.insert(tk.END, "CODE CHANGE:\n")
                        self.suggestions_text.insert(tk.END, suggestion["code"] + "\n\n")
                
                elif pattern["type"] == "missing" and pattern["base"] != "Any":
                    base = pattern["base"]
                    mixer = pattern["mixer"]
                    effect = pattern["effect"]
                    
                    suggestion = {
                        "type": "add_effect",
                        "base": base,
                        "mixer": mixer,
                        "effect": effect,
                        "code": f'# Add to get_effects_from_mixers in calculator.py\n'
                               f'# Special case for {base} with {mixer}\n'
                               f'if base_product == "{base}" and "{mixer}" in mixer_list:\n'
                               f'    if "{effect}" not in effects:\n'
                               f'        effects.append("{effect}")'
                    }
                    
                    self.pattern_suggestions.append(suggestion)
                    
                    self.suggestions_text.insert(tk.END, f"SUGGESTION: When mixing {base} with {mixer},\n")
                    self.suggestions_text.insert(tk.END, f"'{effect}' effect is missing and should be added.\n\n")
                    self.suggestions_text.insert(tk.END, "CODE CHANGE:\n")
                    self.suggestions_text.insert(tk.END, suggestion["code"] + "\n\n")
        
        # 2. Value prediction suggestions
        if self.value_discrepancies:
            self.suggestions_text.insert(tk.END, "=== Market Value Calculation Improvements ===\n\n")
            
            # Group by base product
            base_discrepancies = {}
            for key, discrepancy in self.value_discrepancies.items():
                base, mixer = key
                if base not in base_discrepancies:
                    base_discrepancies[base] = []
                base_discrepancies[base].append(discrepancy)
            
            # Look for consistent patterns within each base
            for base, discrepancies in base_discrepancies.items():
                # Check if we have specific combinations to handle
                for disc in discrepancies:
                    mixer = disc["mixer"]
                    predicted = disc["predicted"]
                    actual = disc["actual"]
                    
                    suggestion = {
                        "type": "override_value",
                        "base": base,
                        "mixer": mixer,
                        "predicted": predicted,
                        "actual": actual,
                        "code": f'# Add to calculate_market_value in calculator.py\n'
                               f'# Special case for {base} + {mixer}\n'
                               f'if base_product == "{base}" and "{mixer}" in mixer_list:\n'
                               f'    return {actual}  # Override calculated value to match in-game'
                    }
                    
                    self.pattern_suggestions.append(suggestion)
                    
                    self.suggestions_text.insert(tk.END, f"SUGGESTION: When mixing {base} with {mixer},\n")
                    self.suggestions_text.insert(tk.END, f"market value should be ${actual} (not ${predicted}).\n\n")
                    self.suggestions_text.insert(tk.END, "CODE CHANGE:\n")
                    self.suggestions_text.insert(tk.END, suggestion["code"] + "\n\n")
    
    def export_suggestions(self):
        """Export code suggestions to a file"""
        if not hasattr(self, 'pattern_suggestions') or not self.pattern_suggestions:
            messagebox.showinfo("Info", "No suggestions to export. Run analysis first.")
            return
        
        try:
            with open("code_suggestions.txt", "w") as f:
                f.write("SCHEDULE I CALCULATOR CODE IMPROVEMENT SUGGESTIONS\n")
                f.write("=================================================\n\n")
                
                f.write("Based on analysis of testing data from: " + self.data_file + "\n\n")
                
                # Effect improvements
                f.write("EFFECT PREDICTION IMPROVEMENTS\n")
                f.write("-----------------------------\n\n")
                
                effect_suggestions = [s for s in self.pattern_suggestions if s["type"] in ("effect_replacement", "add_effect")]
                if effect_suggestions:
                    for i, suggestion in enumerate(effect_suggestions, 1):
                        f.write(f"Suggestion {i}: ")
                        
                        if suggestion["type"] == "effect_replacement":
                            f.write(f"When mixing {suggestion['base']} with {suggestion['mixer']}, ")
                            f.write(f"'{suggestion['wrong_effect']}' should be replaced with '{suggestion['correct_effect']}'.\n\n")
                        else:
                            f.write(f"When mixing {suggestion['base']} with {suggestion['mixer']}, ")
                            f.write(f"'{suggestion['effect']}' effect is missing and should be added.\n\n")
                            
                        f.write("CODE CHANGE:\n")
                        f.write(suggestion["code"] + "\n\n")
                else:
                    f.write("No effect prediction improvements suggested.\n\n")
                
                # Value improvements
                f.write("MARKET VALUE CALCULATION IMPROVEMENTS\n")
                f.write("-----------------------------------\n\n")
                
                value_suggestions = [s for s in self.pattern_suggestions if s["type"] == "override_value"]
                if value_suggestions:
                    for i, suggestion in enumerate(value_suggestions, 1):
                        f.write(f"Suggestion {i}: ")
                        f.write(f"When mixing {suggestion['base']} with {suggestion['mixer']}, ")
                        f.write(f"market value should be ${suggestion['actual']} (not ${suggestion['predicted']}).\n\n")
                        
                        f.write("CODE CHANGE:\n")
                        f.write(suggestion["code"] + "\n\n")
                else:
                    f.write("No market value calculation improvements suggested.\n\n")
            
            messagebox.showinfo("Success", "Suggestions exported to code_suggestions.txt")
        except Exception as e:
            messagebox.showerror("Error", f"Export failed: {str(e)}")


def main():
    root = tk.Tk()
    app = ScheduleIAnalyzerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()