from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich import box
import openmatrix as opmx
import sys
import os
import subprocess
import json
import csv

# WARNING: Moving this file may break functionality due to relative paths.
# Make sure to move this file carefully and ensure /records is a directory
# behind this script.

SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
RECORDS_PATH = os.path.join(SCRIPT_PATH, "..", "records")
RESULTS_PATH = os.path.join(SCRIPT_PATH, "..", "results")
CONFIG_NAME = "config.json"

console = Console()

def genmeshes():
    json_file = open(os.path.join(SCRIPT_PATH, CONFIG_NAME), "r")
    fields = json.load(json_file)
    json_file.close()

    csv_name = os.path.join(RESULTS_PATH, "data.csv")
    os.system("touch " + csv_name)
    csv_file = open(csv_name, "w", newline="")
    writer = csv.writer(csv_file)
    writer.writerow(['id', 'circles', 'vms_max', 'vms_mean', 'area_fraction', 'size'])
    csv_file.close()

    ramp_circle_value = fields["ramp_circles_params"]["start"]
    ramp_layout_value = [fields["ramp_layout_params"]["start_x"], fields["ramp_layout_params"]["start_y"]]

    model = fields["model_form"]

    arg = ""
    if model == "plot":
        arg = "-m"
    elif model == "histogramxy":
        arg = "-b"
    elif model == "histcount":
        arg = "-bc"
    elif model == "meanvis":
        arg = "-bv"

    for i in range(fields["cycles"]):
        if not os.path.exists(RECORDS_PATH):
            os.mkdir(RECORDS_PATH)
        path_name = RECORDS_PATH + "/" + str(i)
        if os.path.exists(path_name):
            os.system("rm -rf " + path_name)
        os.mkdir(path_name)
        mesh_save_path = path_name + "/mesh" + str(i) + ".xdmf"
        console.log(f"[green]Generating mesh {str(i)} stored at {mesh_save_path}[/green]")

        generator = opmx.MeshGenerator(
            layout=fields["layout"] if not fields["ramp_layout"] else ramp_layout_value,
            size=fields["size"],
            mesh_element_size=fields["mesh_element_size"],
            circles=fields["circles"] if not fields["ramp_circles"] else ramp_circle_value,
            randomized_max_radius=fields["randomized_max_radius"],
            circ_distribution_type=fields["distribution"],
            set_circle_radius=fields["set_circle_radius"],
            randomized_radius=fields["randomized_radius"],
            min_fraction_inside=fields["min_fraction_inside"],
            circ_af=[fields["control_af"], fields["af_options"]["const_percentage"], fields["af_options"]["error_bound_percentage"]]
        )
        generator.generate(save_path=mesh_save_path, visualize=False)

        analysis_path = os.path.join(SCRIPT_PATH, "analysis.py")
        model_path = os.path.join(SCRIPT_PATH, "model.py")
        try:
            create_files = "0"
            if fields["create_mesh_files"]:
                create_files = "1"
            subprocess.run(
                [
                    "mpirun", "-np", "1", "python3", 
                    analysis_path, 
                    mesh_save_path, 
                    RESULTS_PATH, 
                    os.path.join(SCRIPT_PATH, CONFIG_NAME), 
                    create_files
                ],
                cwd=path_name,
                check=True
            )
            console.log(f"[green]Analysis complete for mesh {i}[/green]")
        except subprocess.CalledProcessError as e:
            console.log(f"[green]Analysis failed for mesh {i}: {e}[/green]")
        ramp_circle_value += fields["ramp_circles_params"]["step"]
        ramp_layout_value[0] += fields["ramp_layout_params"]["step_x"]
        ramp_layout_value[1] += fields["ramp_layout_params"]["step_y"]
        
    try:
        subprocess.run(
            ["python3", model_path, arg, RESULTS_PATH],
            check=True
        )
        console.log(f"[green]Model completed[/green]")
    except subprocess.CalledProcessError as e:
        console.log(f"[green]Modeling Failed: {e}[/green]")

def intro():
    json_file = open(os.path.join(SCRIPT_PATH, CONFIG_NAME), "r")
    fields = json.load(json_file)

    model = "Mutable Circles Count Analysis"
    if fields["control_af"]:
        model = "Mutable Area Fraction Analysis"
    
    cycles = str(fields["cycles"])
    size = str(fields["size"])
    layout = str(fields["layout"][0]) + "x" + str(fields["layout"][1])
    chart = fields["model_form"]


    console = Console()
    msg = Text()
    msg.append("Version: ", style="bold cyan")
    msg.append("v1.0\n")
    msg.append("Model: ", style="bold cyan")
    msg.append(model + "\n")
    msg.append("Cycles: ", style="bold cyan")
    msg.append(cycles + "\n")
    msg.append("Size: ", style="bold cyan")
    msg.append(size + "\n")
    msg.append("Layout: ", style="bold cyan")
    msg.append(layout + "\n")
    msg.append("Chart: ", style="bold cyan")
    msg.append(chart + "\n")


    panel = Panel(
        msg,
        border_style="bright_blue",
        title="OpenMATRIX",
        padding=(1, 2),
        expand=False,
        box=box.ROUNDED
    )

    console.print(panel)

def main():
    if len(sys.argv) > 1:
        if sys.argv[1] == "-g":
            intro()
            genmeshes()
        elif sys.argv[1] == "-c":
            os.system("rm -rf " + RECORDS_PATH + "/*")
        else:
            console.log("[red]Please read command specifications for main.py[/red]")
            print("Invalid command. Use -g <number> to generate meshes or -c to clear records.")
    else:
        console.log("[red]Please read command specifications for main.py[/red]")
        print("Invalid command. Use -g <number> to generate meshes or -c to clear records.")
    
if __name__ == "__main__":
    main()