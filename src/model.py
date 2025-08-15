import matplotlib.pyplot as plt
import numpy as np
import os
import sys
import csv
import json

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

def generate_binned_count(x_field, y_field, bins=10):
    # Load target area fraction from input.json
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'input.json'), 'r') as f:
        data = json.load(f)
        target_area_fraction = data["af_options"]["const_percentage"]

    x_data = []

    with open(results_file, mode='r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            try:
                x_data.append(float(row[x_field]))
            except ValueError:
                print(f"Skipping invalid row: {row}")

    bin_counts = np.zeros(bins)
    bin_edges = np.linspace(min(x_data), max(x_data), bins + 1)

    # Use right=True to include the last bin edge correctly
    for x in x_data:
        bin_index = np.digitize(x, bin_edges, right=True) - 1
        if 0 <= bin_index < bins:
            bin_counts[bin_index] += 1

    bin_centers = 0.5 * (bin_edges[:-1] + bin_edges[1:])

    # Plot counts
    plt.figure(figsize=(8, 5))
    plt.bar(bin_centers, bin_counts, width=(bin_edges[1] - bin_edges[0]),
            align='center', edgecolor='black')

    plt.xlabel(x_field)
    plt.ylabel(f"Count of {x_field} in bin")
    plt.title(f"Counts binned by {x_field} for target area fraction of {target_area_fraction}")

    # Side note for target area fraction
    plt.text(1.02, 0.5, f"Target area fraction: {target_area_fraction}",
             transform=plt.gca().transAxes, rotation=90,
             va='center', ha='left', fontsize=10, color='blue')

    plt.tight_layout()

    filename = f"{x_field}_count_bins.png"
    save_path = os.path.join(results_path, filename)
    plt.savefig(save_path)
    print(f"Binned count histogram saved to: {save_path}")
    plt.show()

def generate_binned_xy(x_field, y_field, bins=10):
    x_data = []
    y_data = []

    with open(results_file, mode='r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            try:
                x_data.append(float(row[x_field]))
                y_data.append(float(row[y_field]))
            except ValueError:
                print(f"Skipping invalid row: {row}")

    bin_sums = np.zeros(bins)
    bin_counts = np.zeros(bins)
    bin_edges = np.linspace(min(x_data), max(x_data), bins + 1)

    for x, y in zip(x_data, y_data):
        bin_index = np.digitize(x, bin_edges) - 1
        if 0 <= bin_index < bins:
            bin_sums[bin_index] += y
            bin_counts[bin_index] += 1

    bin_means = bin_sums / np.maximum(bin_counts, 1)
    bin_centers = 0.5 * (bin_edges[:-1] + bin_edges[1:])

    # Plot
    plt.figure(figsize=(8, 5))
    plt.bar(bin_centers, bin_means, width=(bin_edges[1] - bin_edges[0]), align='center', edgecolor='black')
    plt.xlabel(x_field)
    plt.ylabel(f"Mean {y_field}")
    plt.title(f"{y_field} binned by {x_field}")
    plt.tight_layout()

    filename = f"{x_field}_vs_{y_field}_binned.png"
    save_path = os.path.join(results_path, filename)
    plt.savefig(save_path)
    print(f"Binned histogram saved to: {save_path}")
    plt.show()

def generate_binned_histogram(x_field, y_field, bins=10):
    x_data = []
    y_data = []

    with open(results_file, mode='r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            try:
                x_data.append(float(row[x_field]))
                y_data.append(float(row[y_field]))
            except ValueError:
                print(f"Skipping invalid row: {row}")

    bin_sums = np.zeros(bins)
    bin_counts = np.zeros(bins)
    bin_edges = np.linspace(min(x_data), max(x_data), bins + 1)

    for x, y in zip(x_data, y_data):
        bin_index = np.digitize(x, bin_edges) - 1
        if 0 <= bin_index < bins:
            bin_sums[bin_index] += y
            bin_counts[bin_index] += 1

    bin_means = bin_sums / np.maximum(bin_counts, 1)
    bin_centers = 0.5 * (bin_edges[:-1] + bin_edges[1:])

    # Plot
    plt.figure(figsize=(8, 5))
    plt.bar(bin_centers, bin_means, width=(bin_edges[1] - bin_edges[0]), align='center', edgecolor='black')
    plt.xlabel(x_field)
    plt.ylabel(f"Mean {y_field}")
    plt.title(f"{y_field} binned by {x_field}")
    plt.tight_layout()

    filename = f"{x_field}_vs_{y_field}_binned.png"
    save_path = os.path.join(results_path, filename)
    plt.savefig(save_path)
    print(f"Binned histogram saved to: {save_path}")
    plt.show()


def controller():
    if sys.argv[1] == "-m":
        x_field = "circles"
        y_field = "vms_max"
        generate_matplot(x_field, y_field)
    elif sys.argv[1] == "-b":
        x_field = "vms_max"
        y_field = "area_fraction"
        generate_binned_histogram(x_field, y_field, bins=10)
    elif sys.argv[1] == "-bc":
        x_field = "vms_max"
        y_field = "area_fraction"
        generate_binned_count(x_field, y_field, bins=10)
    else:
        print("Usage: python3 main.py -m")
        print("This will generate a matplot model")
        print("\n")
        print("Usage: python3 main.py -b")
        print("This will generate a binned histogram model")

if __name__ == "__main__":
    controller()