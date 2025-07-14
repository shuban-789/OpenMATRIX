# armgen2d

`armgen2d` stands for `a random mesh generator (2d)` and is used to create 2D meshes via `gmsh` with circles of varying distribution. Parameters can also be controlled.

```
Use -g <number> to generate meshes or -c to clear records.
```

Docker:
```
sudo docker run -it --rm -v "$(pwd)":/workspace:z dolfinx/dolfinx:v0.6.0
```

Input:
```
{
    "cycles":  50,
    "layout":  [4, 4],
    "size":  0.01,
    "circles":  10,
    "ramp_circles":  true,
    "ramp_circles_params":  {
        "start":  3,
        "step":  2
    },
    "randomized_max_radius":  0.5,
    "distribution":  "gaussian",
    "set_circle_radius":  0.5,
    "mesh_element_size":  0.1,
    "randomized_radius":  true,
    "min_fraction_inside":  0.2,
    "create_mesh_files":  false,
    "model_form":  "plot"
}
```

- Distribution field can be changed to `uniform`
- Model form fieldd can be changed to `histogram`
- The fiield `set_circle_radius` does NOT apply if `randomized_radius` is set to true