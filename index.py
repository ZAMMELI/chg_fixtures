import sys
import os
from os import path
import glob
import datetime
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QPushButton
from PyQt5.QtCore import Qt
from PyQt5.QtGui import *
from PyQt5.uic import loadUiType

# Path for the file
file_path = r"K:\Agilent_ICT\Boards\Status" # original path


# Load UI from .ui file (Create this UI with Qt Designer)
FORM_CLASS, _ = loadUiType(path.join(path.dirname(__file__), 'CH_counter.ui'))


class MainApp(QWidget, FORM_CLASS):
    def __init__(self, parent=None):
        super(MainApp, self).__init__(parent)
        self.setupUi(self)  # Initialize the UI components from .ui file
        self.setWindowTitle("Changes_Counter interfaces")

        # Initialize your custom labels and buttons
        self.source_label.setText("Source: Not selected")
        self.change_label.setText("Nb de changements :")
        self.lcd_display.display(0)


        # Connect the button to the process_file method
        self.start_button.clicked.connect(self.process_file)

    def process_file(self):
        """Process the second-to-last file in the directory and update the count."""
        files = glob.glob(os.path.join(file_path, "*"))
        if len(files) < 2:
            self.source_label.setText("Source: Not enough files")
            return

        # Get the second most recent file
        myfile = sorted(files, key=os.path.getmtime, reverse=True)[1]
        self.source_label.setText(f"Source: {os.path.basename(myfile)}")

        total_changes, interface_change_count = self.count_changes(myfile)
        self.lcd_display.display(str(total_changes))

        # Plot the graph if interface changes are present
        if interface_change_count:
            self.plot_graph(interface_change_count)

    def count_changes(self, filename):
        """Counts the number of interface changes based on the logic provided."""
        interface_tracker = {}
        interface_change_count = {}
        total_changes = 0

        def parse_time(hour, minute):
            try:
                return datetime.datetime.strptime(f"{hour.strip()}:{minute.strip()}", "%H:%M")
            except ValueError:
                return None

        try:
            with open(filename, "r") as infile:
                for line in infile:
                    fields = line.strip().split("|")
                    if len(fields) != 7:
                        continue

                    date, hour, minute, pcname, autofile, interface, ref = fields
                    current_time = parse_time(hour, minute)
                    if current_time is None:
                        continue

                    change_reason = ""

                    if interface in interface_tracker:
                        last_time, last_pcname = interface_tracker[interface]
                        time_difference = (current_time - last_time).total_seconds() / 60

                        if last_pcname != pcname:
                            change_reason = "✅ (PC Changed)"
                        elif time_difference > 120:
                            change_reason = "✅ (Time > 2h)"

                        if change_reason:
                            total_changes += 1
                            interface_change_count[interface] = interface_change_count.get(interface, 0) + 1
                    else:
                        change_reason = "✅ (First Appearance)"
                        total_changes += 1
                        interface_change_count[interface] = 1

                    interface_tracker[interface] = (current_time, pcname)

        except FileNotFoundError:
            self.source_label.setText("Error: File not found")
        except Exception as e:
            self.source_label.setText(f"Error: {e}")

        return total_changes, interface_change_count

    def plot_graph(self, interface_change_count):
        """Plots a bar chart for interface changes."""
        interfaces = list(interface_change_count.keys())
        change_counts = list(interface_change_count.values())

        plt.figure(figsize=(10, 6))
        plt.bar(interfaces, change_counts, color='skyblue')
        plt.xlabel('Interfaces')
        plt.ylabel('Number of Changes')
        plt.title('Interface Changes Visualization')

        # Ensure the y-axis has integer values
        plt.gca().yaxis.set_major_locator(MaxNLocator(integer=True))

        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        plt.show()


def main():
    app = QApplication(sys.argv)
    window = MainApp()
    window.show()
    sys.exit(app.exec_())  # Ensure correct application exit


if __name__ == '__main__':
    main()
