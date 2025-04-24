import armgen2d
import sys
import os

def genmeshes(number):
    for i in range(number):
        if not os.path.exists("../records/"):
            os.mkdir("../records/")
        path_name = "../records/" + str(i)
        os.mkdir(path_name)
        savepath = path_name + "/mesh" + str(i) + ".xdmf"
        layout = (4, 4)
        size = 0.01
        circles = 5
        randomized_max_radius = 0.5
        distribution = "gaussian"
        set_circle_radius = 0.5
        mesh_element_size = 0.1
        randomized_radius = True
        generator = armgen2d.MeshGenerator(
            layout=layout,
            size=size,
            mesh_element_size=mesh_element_size,
            circles=circles,
            randomized_max_radius=randomized_max_radius,
            distribution=distribution,
            set_circle_radius=set_circle_radius,
            randomized_radius=randomized_radius
        )
        generator.generate(save_path=savepath)

def main():
    if len(sys.argv) > 1:
        if sys.argv[1] == "-g" and len(sys.argv) == 3:
            os.system("rm -rf ../records/*")
            number = int(sys.argv[2])
            genmeshes(number)
        elif sys.argv[1] == "-c":
            os.system("rm -rf ../records/*")
        else:
            print("Invalid command. Use -g <number> to generate meshes or -c to clear records.")
    else:
        print("Invalid command. Use -g <number> to generate meshes or -c to clear records.")
    
if __name__ == "__main__":
    main()