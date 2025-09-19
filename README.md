# OpenMATRIX

## Intro

OpenMATRIX (Open Multiphysics Analysis and Templating for Randomized Infinitesmal compleXes) is a lightweight framework designed for multiphysics research involving micro-architectures. It can generate 2D finite element meshes by simulating particles within a domain using circles. The framework automates mesh generation based on provided parameters and can produce graphs according to user specifications. To run it, the only required inputs are the analysis to perform, a set of dataset parameters, and a configured JSON input file.

The setup supports running the software through the use of a makefile. Once you have `input.json` configured, run your study through the `make` command.

```bash
make # run study
make clean # clean files
```

## Input

```
{
    "cycles":  1,
    "layout":  [4, 4],
    "size":  0.01,
    "distribution":  "gaussian",
    "mesh_element_size":  0.1,
    "min_fraction_inside":  0.2,
    "model_form":  "meanvis",
    "create_mesh_files":  false,
    "randomized_radius":  true,
    "random_params": {
        "randomized_max_radius":  0.5
    },
    "ramp_layout": false,
    "ramp_layout_params": {
        "start_x": 1,
        "step_x": 1,
        "start_y": 1,
        "step_y": 1
    },
    "control_af": true,
    "af_options": {
        "const_percentage": 30.0,
        "error_bound_percentage": 1.5
    },
    "ramp_circles":  false,
    "ramp_circles_params":  {
        "start":  3,
        "step":  2
    },
    "control_circles": false,
    "control_circles_params": {
        "set_circle_radius": 0.5,
        "circles": 10
    }
}
```

- Distribution field can be changed to `uniform`
- Model form fieldd can be changed to `histogram`
- The field `set_circle_radius` does NOT apply if `randomized_radius` is set to true

> WARNING: This software has 0 documentation at all and has minimal standardization. Right now it is tailored toward personal research endeavors. Tailoring functionality for a specific project may need minimal but gaurunteed changes in code.

## Docker

If you do not have the fenics environment setup on your host, you may use a Docker image to run this code. Just run the code below as follows after pulling the dolfinx enviornment container.

Interactive shell:

```
sudo docker pull dolfinx/dolfinx:v0.9.0
sudo docker run -it --rm -v "$(pwd)":/workspace:z dolfinx/dolfinx:v0.9.0
pip install rich pathlib
```
```
make
```

Dockerfile:

```
sudo docker build -t <some_name> .
sudo docker run -t --rm <image_name>
```