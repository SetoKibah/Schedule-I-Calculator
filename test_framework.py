"""
Schedule I Testing Framework
Helps systematically document and verify in-game combinations and their effects.
"""

import json
import os
import tkinter as tk
from tkinter import ttk, messagebox
from src.game_data import MARIJUANA_STRAINS, MIXERS, EFFECTS
from src.calculator import calculate_market_value, calculate_product_cost, get_effects_from_mixers


class ScheduleITestingApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Schedule I Testing Framework")
        self.root.geometry("800x700")
        
        # Data file path
        self.data_file = "testing_data.json"
        
        # Load existing test data if available
        self.test_data = self.load_test_data()
        
        self.setup_ui()
    
    def load_test_data(self):
        """Load existing test data from file"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return {"combinations": []}
        return {"combinations": []}
    
    def save_test_data(self):
        """Save test data to file"""
        with open(self.data_file, 'w') as f:
            json.dump(self.test_data, f, indent=4)
        messagebox.showinfo("Success", "Test data saved successfully!")
    
    def setup_ui(self):
        """Set up the user interface"""
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Add tabs
        self.add_test_frame = ttk.Frame(notebook)
        self.view_test_frame = ttk.Frame(notebook)
        
        notebook.add(self.add_test_frame, text="Add Test Case")
        notebook.add(self.view_test_frame, text="View Test Data")
        
        self.setup_add_test_tab()
        self.setup_view_test_tab()
    
    def setup_add_test_tab(self):
        """Set up the Add Test Case tab"""
        frame = self.add_test_frame
        
        # Base product selection
        ttk.Label(frame, text="Base Product:").grid(row=0, column=0, sticky="w", padx=10, pady=5)
        self.base_var = tk.StringVar()
        base_combo = ttk.Combobox(frame, textvariable=self.base_var, width=20)
        base_combo['values'] = list(MARIJUANA_STRAINS.keys())
        base_combo.grid(row=0, column=1, sticky="w", padx=10, pady=5)
        base_combo.current(0)
        
        # Mixer selection
        ttk.Label(frame, text="Mixer:").grid(row=1, column=0, sticky="w", padx=10, pady=5)
        self.mixer_var = tk.StringVar()
        mixer_combo = ttk.Combobox(frame, textvariable=self.mixer_var, width=20)
        mixer_combo['values'] = list(MIXERS.keys())
        mixer_combo.grid(row=1, column=1, sticky="w", padx=10, pady=5)
        mixer_combo.current(0)
        
        # Predicted results from calculator
        ttk.Label(frame, text="Predicted Results:").grid(row=2, column=0, sticky="w", padx=10, pady=5)
        self.prediction_text = tk.Text(frame, height=6, width=60)
        self.prediction_text.grid(row=3, column=0, columnspan=2, sticky="w", padx=10, pady=5)
        self.prediction_text.config(state=tk.DISABLED)
        
        # Calculate button
        ttk.Button(frame, text="Calculate Prediction", command=self.calculate_prediction).grid(row=4, column=0, columnspan=2, padx=10, pady=5)
        
        # Separator
        ttk.Separator(frame, orient=tk.HORIZONTAL).grid(row=5, column=0, columnspan=2, sticky="ew", padx=10, pady=10)
        
        # Actual in-game results
        ttk.Label(frame, text="Actual In-Game Results:").grid(row=6, column=0, sticky="w", padx=10, pady=5)
        
        ttk.Label(frame, text="Actual Effects (comma-separated):").grid(row=7, column=0, sticky="w", padx=10, pady=5)
        self.actual_effects_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.actual_effects_var, width=40).grid(row=7, column=1, sticky="w", padx=10, pady=5)
        
        ttk.Label(frame, text="Actual Market Value ($):").grid(row=8, column=0, sticky="w", padx=10, pady=5)
        self.actual_value_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.actual_value_var, width=10).grid(row=8, column=1, sticky="w", padx=10, pady=5)
        
        ttk.Label(frame, text="Notes:").grid(row=9, column=0, sticky="w", padx=10, pady=5)
        self.notes_text = tk.Text(frame, height=4, width=60)
        self.notes_text.grid(row=10, column=0, columnspan=2, sticky="w", padx=10, pady=5)
        
        # Save button
        ttk.Button(frame, text="Save Test Case", command=self.save_test_case).grid(row=11, column=0, columnspan=2, padx=10, pady=10)
    
    def setup_view_test_tab(self):
        """Set up the View Test Data tab"""
        frame = self.view_test_frame
        
        # Create treeview
        columns = ("Base", "Mixer", "Predicted Effects", "Actual Effects", "Predicted Value", "Actual Value")
        self.tree = ttk.Treeview(frame, columns=columns, show="headings", height=15)
        
        # Configure headings
        for col in columns:
            self.tree.heading(col, text=col)
            if col in ("Predicted Effects", "Actual Effects"):
                self.tree.column(col, width=150)
            else:
                self.tree.column(col, width=80)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        
        # Pack tree and scrollbar
        self.tree.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        scrollbar.grid(row=0, column=1, sticky="ns", pady=10)
        
        # Details section
        ttk.Label(frame, text="Details:").grid(row=1, column=0, sticky="w", padx=10, pady=5)
        self.details_text = tk.Text(frame, height=10, width=70)
        self.details_text.grid(row=2, column=0, sticky="nsew", padx=10, pady=5)
        self.details_text.config(state=tk.DISABLED)
        
        # Buttons
        button_frame = ttk.Frame(frame)
        button_frame.grid(row=3, column=0, sticky="w", padx=10, pady=10)
        
        ttk.Button(button_frame, text="Refresh Data", command=self.refresh_test_data).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Export to CSV", command=self.export_to_csv).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Delete Selected", command=self.delete_selected).pack(side=tk.LEFT, padx=5)
        
        # Configure weight
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)
        frame.rowconfigure(2, weight=1)
        
        # Bind selection event
        self.tree.bind("<<TreeviewSelect>>", self.show_details)
        
        # Load initial data
        self.refresh_test_data()
    
    def calculate_prediction(self):
        """Calculate predicted results based on current selection"""
        base = self.base_var.get()
        mixer = self.mixer_var.get()
        
        if not base or not mixer:
            return
        
        effects = get_effects_from_mixers(base, [mixer])
        market_value = calculate_market_value(base, effects)
        total_cost = calculate_product_cost(base, [mixer])
        profit = market_value - total_cost
        profit_margin = (profit / total_cost) * 100 if total_cost > 0 else 0
        
        self.prediction_text.config(state=tk.NORMAL)
        self.prediction_text.delete(1.0, tk.END)
        
        self.prediction_text.insert(tk.END, f"Base: {base}\n")
        self.prediction_text.insert(tk.END, f"Mixer: {mixer}\n")
        self.prediction_text.insert(tk.END, f"Predicted Effects: {', '.join(effects)}\n")
        self.prediction_text.insert(tk.END, f"Predicted Market Value: ${market_value}\n")
        self.prediction_text.insert(tk.END, f"Production Cost: ${total_cost}\n")
        self.prediction_text.insert(tk.END, f"Profit Margin: {profit_margin:.1f}%\n")
        
        self.prediction_text.config(state=tk.DISABLED)
    
    def save_test_case(self):
        """Save the current test case to the test data"""
        base = self.base_var.get()
        mixer = self.mixer_var.get()
        
        if not base or not mixer:
            messagebox.showerror("Error", "Please select a base product and mixer")
            return
        
        try:
            actual_value = int(self.actual_value_var.get()) if self.actual_value_var.get() else None
        except ValueError:
            messagebox.showerror("Error", "Market value must be a number")
            return
        
        actual_effects = [e.strip() for e in self.actual_effects_var.get().split(",")] if self.actual_effects_var.get() else []
        notes = self.notes_text.get(1.0, tk.END).strip()
        
        # Calculate prediction
        predicted_effects = get_effects_from_mixers(base, [mixer])
        predicted_value = calculate_market_value(base, predicted_effects)
        total_cost = calculate_product_cost(base, [mixer])
        profit = (actual_value or predicted_value) - total_cost
        profit_margin = (profit / total_cost) * 100 if total_cost > 0 else 0
        
        # Create test case data
        test_case = {
            "base": base,
            "mixer": mixer,
            "predicted_effects": predicted_effects,
            "actual_effects": actual_effects,
            "predicted_value": predicted_value,
            "actual_value": actual_value,
            "production_cost": total_cost,
            "profit_margin": profit_margin,
            "notes": notes
        }
        
        # Save to test data
        self.test_data["combinations"].append(test_case)
        self.save_test_data()
        
        # Refresh and clear form
        self.refresh_test_data()
        self.actual_effects_var.set("")
        self.actual_value_var.set("")
        self.notes_text.delete(1.0, tk.END)
    
    def refresh_test_data(self):
        """Refresh the test data view"""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Insert test cases
        for i, case in enumerate(self.test_data["combinations"]):
            self.tree.insert("", tk.END, iid=str(i), values=(
                case["base"],
                case["mixer"],
                ", ".join(case["predicted_effects"]),
                ", ".join(case["actual_effects"]),
                f"${case['predicted_value']}",
                f"${case['actual_value']}" if case['actual_value'] else "N/A"
            ))
    
    def show_details(self, event):
        """Show details of the selected test case"""
        selected = self.tree.selection()
        if not selected:
            return
        
        case_index = int(selected[0])
        case = self.test_data["combinations"][case_index]
        
        self.details_text.config(state=tk.NORMAL)
        self.details_text.delete(1.0, tk.END)
        
        self.details_text.insert(tk.END, f"Base: {case['base']}\n")
        self.details_text.insert(tk.END, f"Mixer: {case['mixer']}\n\n")
        
        self.details_text.insert(tk.END, f"Predicted Effects: {', '.join(case['predicted_effects'])}\n")
        self.details_text.insert(tk.END, f"Actual Effects: {', '.join(case['actual_effects'])}\n\n")
        
        self.details_text.insert(tk.END, f"Predicted Market Value: ${case['predicted_value']}\n")
        if case['actual_value']:
            self.details_text.insert(tk.END, f"Actual Market Value: ${case['actual_value']}\n")
        
        self.details_text.insert(tk.END, f"Production Cost: ${case['production_cost']}\n")
        self.details_text.insert(tk.END, f"Profit Margin: {case['profit_margin']:.1f}%\n\n")
        
        if case['notes']:
            self.details_text.insert(tk.END, f"Notes:\n{case['notes']}\n")
        
        self.details_text.config(state=tk.DISABLED)
    
    def export_to_csv(self):
        """Export test data to CSV file"""
        try:
            with open("schedule_i_test_data.csv", "w") as f:
                # Write header
                f.write("Base,Mixer,Predicted Effects,Actual Effects,Predicted Value,Actual Value,Production Cost,Profit Margin,Notes\n")
                
                # Write data
                for case in self.test_data["combinations"]:
                    f.write(f"{case['base']},")
                    f.write(f"{case['mixer']},")
                    f.write(f"\"{','.join(case['predicted_effects'])}\",")
                    f.write(f"\"{','.join(case['actual_effects'])}\",")
                    f.write(f"${case['predicted_value']},")
                    f.write(f"${case['actual_value'] if case['actual_value'] else 'N/A'},")
                    f.write(f"${case['production_cost']},")
                    f.write(f"{case['profit_margin']:.1f}%,")
                    f.write(f"\"{case['notes'].replace(chr(10), ' ').replace('\"', '\"\"')}\"\n")
            
            messagebox.showinfo("Success", "Data exported to schedule_i_test_data.csv")
        except Exception as e:
            messagebox.showerror("Error", f"Export failed: {str(e)}")
    
    def delete_selected(self):
        """Delete the selected test case"""
        selected = self.tree.selection()
        if not selected:
            return
        
        if messagebox.askyesno("Confirm", "Are you sure you want to delete this test case?"):
            case_index = int(selected[0])
            del self.test_data["combinations"][case_index]
            self.save_test_data()
            self.refresh_test_data()


def main():
    root = tk.Tk()
    app = ScheduleITestingApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()