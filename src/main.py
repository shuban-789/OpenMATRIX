import armgen2d
import sys
import os
import subprocess
import json

# WARNING: Moving this file may break functionality due to relative paths.
# Make sure to move this file carefully and ensure /records is a directory
# behind this script.

SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
RECORDS_PATH = os.path.join(SCRIPT_PATH, "..", "records")

def genmeshes():
    json_file = open(os.path.join(SCRIPT_PATH, "input.json"), "r")
    fields = json.load(json_file)
    json_file.close()

    for i in range(fields["cycles"]):
        if not os.path.exists(RECORDS_PATH):
            os.mkdir(RECORDS_PATH)
        path_name = RECORDS_PATH + "/" + str(i)
        if os.path.exists(path_name):
            os.system("rm -rf " + path_name)
        os.mkdir(path_name)
        mesh_save_path = path_name + "/mesh" + str(i) + ".xdmf"
        print("Generating mesh " + str(i) + " stored at " + mesh_save_path)

        generator = armgen2d.MeshGenerator(
            layout=fields["layout"],
            size=fields["size"],
            mesh_element_size=fields["mesh_element_size"],
            circles=fields["circles"],
            randomized_max_radius=fields["randomized_max_radius"],
            distribution=fields["distribution"],
            set_circle_radius=fields["set_circle_radius"],
            randomized_radius=fields["randomized_radius"],
            min_fraction_inside=fields["min_fraction_inside"]
        )
        generator.generate(save_path=mesh_save_path, visualize=False)

        analysis_path = os.path.join(SCRIPT_PATH, "analysis_v2.py")
        try:
            subprocess.run(
                ["mpirun", "-np", "1", "python3", analysis_path, mesh_save_path],
                cwd=path_name,
                check=True
            )
            print(f"Analysis complete for mesh {i}")
        except subprocess.CalledProcessError as e:
            print(f"Analysis failed for mesh {i}: {e}")

def main():
    if len(sys.argv) > 1:
        if sys.argv[1] == "-g":
            genmeshes()
        elif sys.argv[1] == "-c":
            os.system("rm -rf " + RECORDS_PATH + "/*")
        else:
            print("Invalid command. Use -g <number> to generate meshes or -c to clear records.")
    else:
        print("Invalid command. Use -g <number> to generate meshes or -c to clear records.")
    
if __name__ == "__main__":
    main()