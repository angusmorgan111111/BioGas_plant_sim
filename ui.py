import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from model import Shit, FeedStock, feed
from datetime import datetime
import matplotlib
matplotlib.use('TkAgg')  # Set backend before importing pyplot
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np


class BiogasSimulatorUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Biogas Plant Simulator")
        self.root.geometry("1200x900")
        
        # Initialize data
        self.feedstock_obj = None
        self.load_feedstock_data()
        
        # Create main frame
        self.main_frame = ttk.Frame(self.root, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create UI sections
        self.create_header_section()
        self.create_feedstock_section()
        self.create_results_section()
        self.create_bulk_properties_section()
        self.create_chart_section()
        
        # Load default values
        self.load_defaults()
    
    def load_feedstock_data(self):
        """Load feedstock data from CSV"""
        try:
            self.feedstock_obj = feed("Feedstocks_Training.csv")
        except Exception as e:
            messagebox.showerror("Error", f"Error loading feedstock data: {e}")
    
    def create_header_section(self):
        """Create project details and logo section"""
        header_frame = ttk.LabelFrame(self.main_frame, text="Project Details", padding="10")
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Container for left and right sections
        header_container = ttk.Frame(header_frame)
        header_container.pack(fill=tk.X)
        
        # Left side - Project details (fixed width)
        details_frame = ttk.Frame(header_container, width=400)
        details_frame.pack(side=tk.LEFT, fill=tk.Y)
        details_frame.pack_propagate(False)
        
        # Project detail fields
        ttk.Label(details_frame, text="Project Name:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.project_name = ttk.Entry(details_frame, width=30)
        self.project_name.grid(row=0, column=1, sticky=tk.W, padx=(5, 0), pady=2)
        
        ttk.Label(details_frame, text="Location:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.location = ttk.Entry(details_frame, width=30)
        self.location.grid(row=1, column=1, sticky=tk.W, padx=(5, 0), pady=2)
        
        ttk.Label(details_frame, text="Date:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.date = ttk.Entry(details_frame, width=30)
        self.date.grid(row=2, column=1, sticky=tk.W, padx=(5, 0), pady=2)
        
        ttk.Label(details_frame, text="Consultant:").grid(row=3, column=0, sticky=tk.W, pady=2)
        self.consultant = ttk.Entry(details_frame, width=30)
        self.consultant.grid(row=3, column=1, sticky=tk.W, padx=(5, 0), pady=2)
        
        # Right side - Logo space (fixed width)
        logo_frame = ttk.Frame(header_container, width=200, height=100, relief="sunken")
        logo_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(20, 0))
        logo_frame.pack_propagate(False)
        
        self.logo_label = tk.Label(logo_frame, text="Click to add logo", 
                                  bg="lightgray", cursor="hand2")
        self.logo_label.pack(fill=tk.BOTH, expand=True)
        self.logo_label.bind("<Button-1>", self.add_logo)
    
    def create_feedstock_section(self):
        """Create feedstock volume input and results section side by side"""
        main_section_frame = ttk.Frame(self.main_frame, height=225)
        main_section_frame.pack(fill=tk.X, pady=(0, 10))
        main_section_frame.pack_propagate(False)
        
        # Left side - Feedstock Volumes (fixed width)
        feedstock_frame = ttk.LabelFrame(main_section_frame, text="Feedstock Volumes (TPA)", padding="10")
        feedstock_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 2))
        
        # Container for feedstock tree with fixed width
        feedstock_container = ttk.Frame(feedstock_frame, width=350)
        feedstock_container.pack(fill=tk.BOTH, expand=True)
        feedstock_container.pack_propagate(False)
        
        # Create treeview for feedstock volumes
        columns = ("Volume",)
        self.feedstock_tree = ttk.Treeview(feedstock_container, columns=columns, show="tree headings", height=8)
        self.feedstock_tree.heading("#0", text="Feedstock Name")
        self.feedstock_tree.heading("Volume", text="Annual Volume (TPA)")
        self.feedstock_tree.column("#0", width=180, stretch=False)
        self.feedstock_tree.column("Volume", width=150, stretch=False)
        
        # Scrollbar for feedstock tree
        feedstock_scroll = ttk.Scrollbar(feedstock_container, orient="vertical", command=self.feedstock_tree.yview)
        self.feedstock_tree.configure(yscrollcommand=feedstock_scroll.set)
        
        self.feedstock_tree.pack(side="left", fill="both", expand=True)
        feedstock_scroll.pack(side="right", fill="y")
        
        # Enable volume editing
        self.feedstock_tree.bind("<Double-1>", self.edit_volume)
        
        # Load feedstock data
        self.load_feedstock_volumes()
        
        # Run simulation button
        button_frame = ttk.Frame(feedstock_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.run_button = ttk.Button(button_frame, text="Run Simulation", command=self.run_simulation)
        self.run_button.pack(side=tk.LEFT)
        
        # Right side - Biogas Production Statistics (fixed width)
        results_frame = ttk.LabelFrame(main_section_frame, text="Biogas Production Statistics", padding="10")
        results_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(2, 0))
        
        # Container for results tree with fixed width
        results_container = ttk.Frame(results_frame, width=800)
        results_container.pack(fill=tk.BOTH, expand=True)
        results_container.pack_propagate(False)
        
        # Create treeview for Biogas Production Statistics
        columns = ("Volume_TPA", "Biogas_Year", "Biogas_Hour", "Methane_Year", "Methane_Hour", "Energy")
        self.results_tree = ttk.Treeview(results_container, columns=columns, show="tree headings", height=8)
        self.results_tree.heading("#0", text="Feedstock Name")
        self.results_tree.heading("Volume_TPA", text="Volume (TPA)")
        self.results_tree.heading("Biogas_Year", text="Biogas (m³/yr)")
        self.results_tree.heading("Biogas_Hour", text="Biogas (m³/hr)")
        self.results_tree.heading("Methane_Year", text="Methane (m³/yr)")
        self.results_tree.heading("Methane_Hour", text="Methane (m³/hr)")
        self.results_tree.heading("Energy", text="Energy (MWh/yr)")
        
        # Set column widths wide enough for headers and values
        self.results_tree.column("#0", width=120, stretch=False)      # "Feedstock Name"
        self.results_tree.column("Volume_TPA", width=100, stretch=False)   # "Volume (TPA)"
        self.results_tree.column("Biogas_Year", width=110, stretch=False)  # "Biogas (m³/yr)"
        self.results_tree.column("Biogas_Hour", width=110, stretch=False)  # "Biogas (m³/hr)"
        self.results_tree.column("Methane_Year", width=115, stretch=False) # "Methane (m³/yr)"
        self.results_tree.column("Methane_Hour", width=115, stretch=False) # "Methane (m³/hr)"
        self.results_tree.column("Energy", width=120, stretch=False)       # "Energy (MWh/yr)"
        
        # Scrollbar for results
        results_scroll = ttk.Scrollbar(results_container, orient="vertical", command=self.results_tree.yview)
        self.results_tree.configure(yscrollcommand=results_scroll.set)
        
        self.results_tree.pack(side="left", fill="both", expand=True)
        results_scroll.pack(side="right", fill="y")
    
    def create_results_section(self):
        """Results section now handled in create_feedstock_section"""
        pass
    
    def create_bulk_properties_section(self):
        """Create bulk properties and maximum yields tables side by side"""
        bulk_section_frame = ttk.Frame(self.main_frame, height=225)
        bulk_section_frame.pack(fill=tk.X, pady=(10, 0))
        bulk_section_frame.pack_propagate(False)
        
        # Left side - Bulk Properties (fixed width)
        bulk_frame = ttk.LabelFrame(bulk_section_frame, text="Bulk Properties", padding="10")
        bulk_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 2))
        
        # Container for bulk properties tree with fixed width
        bulk_container = ttk.Frame(bulk_frame, width=315)
        bulk_container.pack(fill=tk.BOTH, expand=True)
        bulk_container.pack_propagate(False)
        
        # Create treeview for bulk properties
        columns = ("Value", "Units")
        self.bulk_tree = ttk.Treeview(bulk_container, columns=columns, show="tree headings", height=8)
        self.bulk_tree.heading("#0", text="Property")
        self.bulk_tree.heading("Value", text="Value")
        self.bulk_tree.heading("Units", text="Units")
        self.bulk_tree.column("#0", width=165, stretch=False)
        self.bulk_tree.column("Value", width=90, stretch=False)
        self.bulk_tree.column("Units", width=60, stretch=False)
        
        # Scrollbar for bulk properties
        bulk_scroll = ttk.Scrollbar(bulk_container, orient="vertical", command=self.bulk_tree.yview)
        self.bulk_tree.configure(yscrollcommand=bulk_scroll.set)
        
        self.bulk_tree.pack(side="left", fill="both", expand=True)
        bulk_scroll.pack(side="right", fill="y")
        
        # Right side - Maximum Yields (fixed width)
        yields_frame = ttk.LabelFrame(bulk_section_frame, text="Maximum Gas Yields", padding="10")
        yields_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(2, 0))
        
        # Container for yields tree with fixed width
        yields_container = ttk.Frame(yields_frame, width=315)
        yields_container.pack(fill=tk.BOTH, expand=True)
        yields_container.pack_propagate(False)
        
        # Create treeview for maximum yields
        columns = ("Value", "Units")
        self.yields_tree = ttk.Treeview(yields_container, columns=columns, show="tree headings", height=8)
        self.yields_tree.heading("#0", text="Property")
        self.yields_tree.heading("Value", text="Value")
        self.yields_tree.heading("Units", text="Units")
        self.yields_tree.column("#0", width=165, stretch=False)
        self.yields_tree.column("Value", width=90, stretch=False)
        self.yields_tree.column("Units", width=60, stretch=False)
        
        # Scrollbar for yields
        yields_scroll = ttk.Scrollbar(yields_container, orient="vertical", command=self.yields_tree.yview)
        self.yields_tree.configure(yscrollcommand=yields_scroll.set)
        
        self.yields_tree.pack(side="left", fill="both", expand=True)
        yields_scroll.pack(side="right", fill="y")
    
    def create_chart_section(self):
        """Create chart section below the tables"""
        chart_frame = ttk.LabelFrame(self.main_frame, text="Feedstock Analysis Chart", padding="10")
        chart_frame.pack(fill=tk.X, pady=(10, 0))
        chart_frame.configure(height=600)
        chart_frame.pack_propagate(False)
        
        try:
            # Create matplotlib figure - half width, double height
            self.fig, self.ax = plt.subplots(figsize=(5, 8))
            self.fig.tight_layout(pad=2.0)
            
            self.canvas = FigureCanvasTkAgg(self.fig, chart_frame)
            canvas_widget = self.canvas.get_tk_widget()
            canvas_widget.pack(fill=tk.BOTH, expand=True, pady=5)
            
            # Initial empty plot
            self.ax.text(0.5, 0.5, 'Run simulation to generate chart', 
                        horizontalalignment='center', verticalalignment='center',
                        transform=self.ax.transAxes, fontsize=12, alpha=0.5)
            self.canvas.draw()
        except Exception as e:
            # If matplotlib fails, create a simple label instead
            error_label = tk.Label(chart_frame, text=f"Chart unavailable: {str(e)}", 
                                 fg="red", font=("Arial", 10))
            error_label.pack(fill=tk.X, pady=10)
    
    def load_defaults(self):
        """Load default project values"""
        self.project_name.insert(0, "Biogas Plant Project")
        self.location.insert(0, "Project Location")
        self.date.insert(0, datetime.now().strftime("%d/%m/%Y"))
        self.consultant.insert(0, "Consultant Name")
    
    def load_feedstock_volumes(self):
        """Load feedstock data into volume tree"""
        if not self.feedstock_obj:
            return
        
        # Clear existing items
        for item in self.feedstock_tree.get_children():
            self.feedstock_tree.delete(item)
        
        # Default volumes
        default_volumes = {
            'Cow Slurry': 18500,
            'FYM': 6000,
            'Poultry Litter': 9000,
            'Maize Silage': 15500,
            'DAF Sludges': 2500,
            'Water': 5000
        }
        
        # Add feedstock items
        for feedstock_name in self.feedstock_obj.content.keys():
            volume = default_volumes.get(feedstock_name, 0)
            self.feedstock_tree.insert("", "end", text=feedstock_name, values=(volume,))
            # Set volume in model
            self.feedstock_obj.content[feedstock_name].annual_volume = volume
    
    def add_logo(self, event):
        """Add logo functionality"""
        try:
            filename = filedialog.askopenfilename(
                title="Select Logo Image",
                filetypes=[("Image files", "*.png *.jpg *.jpeg *.gif *.bmp")]
            )
            if filename:
                from PIL import Image, ImageTk
                # Load and resize image
                image = Image.open(filename)
                image = image.resize((180, 80), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(image)
                
                self.logo_label.configure(image=photo, text="")
                self.logo_label.image = photo  # Keep reference
        except Exception as e:
            messagebox.showerror("Error", f"Could not load image: {e}")
    
    def edit_volume(self, event):
        """Allow editing of volume values"""
        item = self.feedstock_tree.selection()
        if not item:
            return
        
        item = item[0]
        column = self.feedstock_tree.identify_column(event.x)
        
        # Check if clicked on the volume column (either #1 or #2 depending on setup)
        if column in ['#1', '#2']:  # Volume column
            try:
                x, y, width, height = self.feedstock_tree.bbox(item, column)
                
                # Create entry widget for editing
                edit_var = tk.StringVar()
                current_value = self.feedstock_tree.set(item, "Volume")
                edit_var.set(current_value)
                
                edit_entry = tk.Entry(self.feedstock_tree, textvariable=edit_var)
                edit_entry.place(x=x, y=y, width=width, height=height)
                edit_entry.focus()
                edit_entry.select_range(0, tk.END)  # Select all text
                
                def save_edit(event=None):
                    new_value = edit_var.get()
                    try:
                        float(new_value)  # Validate numeric input
                        self.feedstock_tree.set(item, "Volume", new_value)
                        edit_entry.destroy()
                    except ValueError:
                        messagebox.showerror("Error", "Please enter a valid number")
                        edit_entry.focus()
                        return
                
                def cancel_edit(event=None):
                    edit_entry.destroy()
                
                edit_entry.bind("<Return>", save_edit)
                edit_entry.bind("<FocusOut>", save_edit)
                edit_entry.bind("<Escape>", cancel_edit)
                
            except tk.TclError:
                # If bbox fails, the item might not be visible
                pass
    
    def run_simulation(self):
        """Run the biogas simulation"""
        try:
            if not self.feedstock_obj:
                messagebox.showerror("Error", "Feedstock data not loaded")
                return
            
            # Update volumes from UI
            for item in self.feedstock_tree.get_children():
                feedstock_name = self.feedstock_tree.item(item, "text")
                volume_str = self.feedstock_tree.set(item, "Volume")
                try:
                    volume = float(volume_str)
                    if feedstock_name in self.feedstock_obj.content:
                        self.feedstock_obj.content[feedstock_name].annual_volume = volume
                except ValueError:
                    messagebox.showerror("Error", f"Invalid volume for {feedstock_name}: {volume_str}")
                    return
            
            # Get production results
            production_df = self.feedstock_obj.biogas_production_stats()
            
            # Get bulk properties and yields
            bulk_df, yields_df = self.feedstock_obj.bulk_properties()
            
            # Clear existing results
            for item in self.results_tree.get_children():
                self.results_tree.delete(item)
            
            # Clear bulk properties and yields tables
            for item in self.bulk_tree.get_children():
                self.bulk_tree.delete(item)
            for item in self.yields_tree.get_children():
                self.yields_tree.delete(item)
            
            # Add results to tree with all Biogas Production Statistics columns
            if production_df is not None and not production_df.empty:
                for _, row in production_df.iterrows():
                    self.results_tree.insert("", "end",
                                           text=row['Feedstock Name'],
                                           values=(
                                               f"{row['Annual Volume (TPA)']:,.0f}",
                                               f"{row['Biogas Volume (m3/yr)']:,.0f}",
                                               f"{row['Biogas Output (m3/hr)']:,.2f}",
                                               f"{row['Methane Volume (m3/yr)']:,.0f}",
                                               f"{row['Methane Output (m3/hr)']:,.2f}",
                                               f"{row['Energy Output (MWh/yr)']:,.1f}"
                                           ))
            
            # Populate bulk properties table
            if bulk_df is not None and not bulk_df.empty:
                for _, row in bulk_df.iterrows():
                    self.bulk_tree.insert("", "end",
                                        text=row['Property'],
                                        values=(
                                            f"{row['Value']:.2f}",
                                            row['Units']
                                        ))
            
            # Populate maximum yields table
            if yields_df is not None and not yields_df.empty:
                for _, row in yields_df.iterrows():
                    self.yields_tree.insert("", "end",
                                          text=row['Property'],
                                          values=(
                                              f"{row['Value']:.2f}",
                                              row['Units']
                                          ))
            
            # Update chart if it exists
            if hasattr(self, 'canvas'):
                self.update_chart()
                
            if production_df is not None and not production_df.empty:
                messagebox.showinfo("Success", "Simulation completed successfully!")
            else:
                messagebox.showwarning("Warning", "No production data generated")
                
        except Exception as e:
            messagebox.showerror("Error", f"Simulation failed: {e}")
    
    def update_chart(self):
        """Update the chart with current simulation data"""
        try:
            # Clear the current plot
            self.ax.clear()
            
            # Get production data
            production_df = self.feedstock_obj.biogas_production_stats()
            
            if production_df is None or production_df.empty:
                self.ax.text(0.5, 0.5, 'No data to display', 
                           horizontalalignment='center', verticalalignment='center',
                           transform=self.ax.transAxes, fontsize=14, alpha=0.5)
                self.canvas.draw()
                return
            
            # Filter out feedstocks with zero volume
            production_df = production_df[production_df['Annual Volume (TPA)'] > 0]
            
            if production_df.empty:
                self.ax.text(0.5, 0.5, 'No feedstocks with volume > 0', 
                           horizontalalignment='center', verticalalignment='center',
                           transform=self.ax.transAxes, fontsize=14, alpha=0.5)
                self.canvas.draw()
                return
            
            # Extract data for plotting
            feedstock_names = production_df['Feedstock Name'].tolist()
            volumes = production_df['Annual Volume (TPA)'].tolist()
            biogas_outputs = (production_df['Biogas Volume (m3/yr)'] / 1000).tolist()  # Convert to thousands
            methane_outputs = (production_df['Methane Volume (m3/yr)'] / 1000).tolist()  # Convert to thousands
            
            # Create the plot
            x = np.arange(len(feedstock_names))
            width = 0.25
            
            # First y-axis for input volumes
            bars1 = self.ax.bar(x - width, volumes, width, label='Feedstock Volume (TPA)', 
                               color='steelblue', alpha=0.8)
            self.ax.set_xlabel('Feedstock Type', fontsize=7)
            self.ax.set_ylabel('Feedstock Volume (TPA)', color='steelblue', fontsize=7)
            self.ax.tick_params(axis='y', labelcolor='steelblue', labelsize=6)
            
            # Second y-axis for gas outputs
            ax2 = self.ax.twinx()
            bars2 = ax2.bar(x, biogas_outputs, width, label='Biogas Volume (1000 m³/yr)', 
                          color='darkorange', alpha=0.8)
            bars3 = ax2.bar(x + width, methane_outputs, width, label='Methane Volume (1000 m³/yr)', 
                          color='forestgreen', alpha=0.8)
            ax2.set_ylabel('Gas Volume (1000 m³/yr)', color='darkred', fontsize=7)
            ax2.tick_params(axis='y', labelcolor='darkred', labelsize=6)
            
            # Customize the plot
            self.ax.set_title('Feedstock Volumes vs Biogas & Methane Production', 
                             fontsize=9, fontweight='bold')
            self.ax.set_xticks(x)
            self.ax.set_xticklabels(feedstock_names, rotation=45, ha='right', fontsize=6)
            
            # Create combined legend
            lines1, labels1 = self.ax.get_legend_handles_labels()
            lines2, labels2 = ax2.get_legend_handles_labels()
            self.ax.legend(lines1 + lines2, labels1 + labels2, loc='upper left', fontsize=6)
            
            # Add value labels on bars
            for bar in bars1:
                height = bar.get_height()
                self.ax.annotate(f'{height:.0f}',
                               xy=(bar.get_x() + bar.get_width() / 2, height),
                               xytext=(0, 3), textcoords="offset points",
                               ha='center', va='bottom', fontsize=6)
            
            for bar in bars2:
                height = bar.get_height()
                ax2.annotate(f'{height:.0f}',
                           xy=(bar.get_x() + bar.get_width() / 2, height),
                           xytext=(0, 3), textcoords="offset points",
                           ha='center', va='bottom', fontsize=6, color='darkorange')
            
            for bar in bars3:
                height = bar.get_height()
                ax2.annotate(f'{height:.0f}',
                           xy=(bar.get_x() + bar.get_width() / 2, height),
                           xytext=(0, 3), textcoords="offset points",
                           ha='center', va='bottom', fontsize=6, color='forestgreen')
            
            # Add grid for better readability
            self.ax.grid(True, alpha=0.3)
            
            # Refresh the canvas
            self.fig.tight_layout(pad=1.5)
            self.canvas.draw()
            
        except Exception as e:
            self.ax.clear()
            self.ax.text(0.5, 0.5, f'Error generating chart: {str(e)}', 
                        horizontalalignment='center', verticalalignment='center',
                        transform=self.ax.transAxes, fontsize=12, alpha=0.7)
            self.canvas.draw()


def main():
    root = tk.Tk()
    app = BiogasSimulatorUI(root)
    
    # Ensure proper cleanup on window close
    def on_closing():
        try:
            # Close matplotlib figures
            plt.close('all')
        except:
            pass
        root.quit()
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    
    try:
        root.mainloop()
    except KeyboardInterrupt:
        on_closing()
    finally:
        # Ensure matplotlib figures are closed
        try:
            plt.close('all')
        except:
            pass


if __name__ == "__main__":
    main()