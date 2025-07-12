import matplotlib.pyplot as plt
import numpy as np
import os
import sys
import csv

results_path = sys.argv[2] if len(sys.argv) > 1 else "results"
results_file = os.path.join(results_path, "data.csv")

def generate_matplot(x_field, y_field):
    x_data = []
    y_data = []

    with open(results_file, mode='r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            try:
                x_data.append(float(row[x_field]))
                y_data.append(float(row[y_field]))
            except ValueError:
                print(f"Skipping row with invalid data: {row}")

    plt.figure(figsize=(8, 5))
    plt.plot(x_data, y_data, marker='o', linestyle='-')
    plt.xlabel(x_field)
    plt.ylabel(y_field)
    plt.title(f'{y_field} vs {x_field}')
    plt.grid(True)
    plt.tight_layout()

    filename = f"{x_field}_{y_field}_mat.png"
    save_path = os.path.join(results_path, filename)
    plt.savefig(save_path)
    print(f"Plot saved to: {save_path}")

    plt.show()

def controller():
    if sys.argv[1] == "-m":
        x_field = "circles"
        y_field = "vms_max"
        generate_matplot(x_field, y_field)
    else:
        print("Usage: python3 main.py -m")
        print("This will generate a matplot model")

if __name__ == "__main__":
    controller()