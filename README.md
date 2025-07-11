# armgen2d

`armgen2d` stands for `a random mesh generator (2d)` and is used to create 2D meshes via `gmsh` with circles of varying distribution. Parameters can also be controlled.

```
Use -g <number> to generate meshes or -c to clear records.
```

Docker:
```
sudo docker run -it --rm -v "$(pwd)":/workspace:z dolfinx/dolfinx:v0.6.0
```