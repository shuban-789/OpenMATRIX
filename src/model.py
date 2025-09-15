from rich.console import Console
import matplotlib.pyplot as plt
import numpy as np
import os
import sys
import csv
import parser

SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
CONFIG_NAME = "config.json"
results_path = sys.argv[2] if len(sys.argv) > 1 else "results"
results_file = os.path.join(results_path, "data.csv")
console = Console()
new_parser = parser.Parser()
fields = new_parser.parsejson(open(os.path.join(SCRIPT_PATH, CONFIG_NAME), "r"))

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
                console.log(f"[red]Skipping row with invalid data: {row}[/red]")

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
    console.log(f"[green]Plot saved to: {save_path}[/green]")

    plt.show()

def generate_binned_count(x_field, y_field, bins=10):
    target_area_fraction = fields["af_options"]["const_percentage"]

    x_data = []

    with open(results_file, mode='r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            try:
                x_data.append(float(row[x_field]))
            except ValueError:
                console.log(f"[red]Skipping invalid row: {row}[/red]")

    bin_counts = np.zeros(bins)
    bin_edges = np.linspace(min(x_data), max(x_data), bins + 1)

    for x in x_data:
        bin_index = np.digitize(x, bin_edges, right=True) - 1
        if 0 <= bin_index < bins:
            bin_counts[bin_index] += 1

    bin_centers = 0.5 * (bin_edges[:-1] + bin_edges[1:])

    plt.figure(figsize=(8, 5))
    plt.bar(bin_centers, bin_counts, width=(bin_edges[1] - bin_edges[0]),
            align='center', edgecolor='black')

    plt.xlabel(x_field)
    plt.ylabel(f"Count of {x_field} in bin")
    plt.title(f"Counts binned by {x_field} for target area fraction of {target_area_fraction}")

    plt.annotate(
        f"Below mean: {below_mean}\nAbove mean: {above_mean}",
        xy=(0.98, 0.95), xycoords="axes fraction",
        ha="right", va="top",
        fontsize=10,
        bbox=dict(facecolor="white", alpha=0.6, edgecolor="black")
    )


    plt.tight_layout()

    filename = f"{x_field}_count_bins.png"
    save_path = os.path.join(results_path, filename)
    plt.savefig(save_path)
    console.log(f"[green]Binned count histogram saved to: {save_path}[/green]")
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
                console.log(f"[red]Skipping invalid row: {row}[/red]")

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
    console.log(f"[green]Binned histogram saved to: {save_path}[/green]")
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
                console.log(f"[red]Skipping invalid row: {row}[/red]")

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
    console.log(f"[green]Binned histogram saved to: {save_path}[/green]")
    plt.show()

def generate_binned_histogram_mean_vis(x_field, bins=10):
    vms_data = []

    target_area_fraction = fields["af_options"]["const_percentage"]

    with open(results_file, mode='r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            try:
                vms_data.append(float(row["vms_max"]))
            except ValueError:
                console.log(f"[red]Skipping invalid row: {row}[/red]")

    if not vms_data:
        console.log("[red]No valid vms_max data found.[/red]")
        return

    vms_mean = np.mean(vms_data)

    plt.figure(figsize=(8, 5))
    counts, bin_edges, _ = plt.hist(vms_data, bins=bins, edgecolor="black", alpha=0.7)

    plt.axvline(vms_mean, color="red", linestyle="--", linewidth=2,
                label=f"Mean vms_max = {vms_mean:.2f}")

    below_mean = np.sum(np.array(vms_data) <= vms_mean)
    above_mean = np.sum(np.array(vms_data) > vms_mean)

    plt.text(vms_mean, max(counts) * 0.9,
             f"Below mean: {below_mean}\nAbove mean: {above_mean}",
             fontsize=10, ha="left", va="top",
             bbox=dict(facecolor="white", alpha=0.6, edgecolor="black"))

    plt.xlabel("vms_max")
    plt.ylabel("Frequency")
    plt.title(f"Counts binned by {x_field} for target area fraction of {target_area_fraction}")
    plt.legend(loc="upper left")
    plt.tight_layout()

    filename = f"vms_max_distribution_area_{target_area_fraction}.png"
    save_path = os.path.join(results_path, filename)
    plt.savefig(save_path)
    console.log(f"[green]VMS max histogram saved to: {save_path}[/green]")
    plt.show()


def controller():
    if sys.argv[1] == "-m":
        x_field = "circles"
        y_field = "vms_mean"
        generate_matplot(x_field, y_field)
    elif sys.argv[1] == "-b":
        x_field = "vms_mean"
        y_field = "area_fraction"
        generate_binned_histogram(x_field, y_field, bins=10)
    elif sys.argv[1] == "-bc":
        x_field = "vms_mean"
        y_field = "area_fraction"
        generate_binned_count(x_field, y_field, bins=10)
    elif sys.argv[1] == "-bv":
        x_field = "vms_max"
        targ = 20
        generate_binned_histogram_mean_vis(x_field, bins=10)
    else:
        console.log("[red]Please read command specifications for model.py[/red]")
        print("Usage: python3 main.py -m")
        print("This will generate a matplot model")
        print("\n")
        print("Usage: python3 main.py -b")
        print("This will generate a binned histogram model")

if __name__ == "__main__":
    controller()