#!/usr/bin/python3
from mpi4py import MPI
from dolfinx.io import gmshio, XDMFFile
from scipy.stats import truncnorm
import gmsh
import random
import math

class MeshGenerator:
    def __init__(self, layout, size, circles, randomized_max_radius, distribution,
                 set_circle_radius, mesh_element_size, randomized_radius):
        self.layout = layout
        self.layout_x = float(layout[0])
        self.layout_y = float(layout[1])
        self.size = size
        self.circles = circles
        self.randomized_max_radius = randomized_max_radius
        self.distribution = distribution
        self.set_circle_radius = set_circle_radius
        self.mesh_element_size = mesh_element_size
        self.randomized_radius = randomized_radius
        self.placed_circles = []

    def check_circ_overlap(self, x1, y1, r1, x2, y2, r2) -> bool:
        d = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
        return d < (r1 + r2)

    def create_rect(self):
        return gmsh.model.occ.addRectangle(0, 0, 0, self.layout_x, self.layout_y)

    def add_circle(self, cx, cy, radius):
        return gmsh.model.occ.addDisk(cx, cy, 0, radius, radius)

    def truncated_gaussian(self, rmin, rmax, rmean, rstd):
        a, b = (rmin - rmean) / rstd, (rmax - rmean) / rstd
        return truncnorm.rvs(a, b, loc=rmean, scale=rstd)

    def generate(self, visualize=True, save_path=None):
        comm = MPI.COMM_WORLD
        rank = comm.rank

        gmsh.initialize()
        gmsh.model.add("Mesh Result")
        gmsh.option.setNumber("Mesh.CharacteristicLengthMax", self.mesh_element_size)

        rect = self.create_rect()
        circle_tags = []

        placed_count = 0
        while placed_count < self.circles:
            valid_placement = False
            while not valid_placement:
                if self.randomized_radius:
                    if self.distribution == "uniform":
                        circle_radius = random.uniform(0.1, self.randomized_max_radius)
                    elif self.distribution == "gaussian":
                        circle_radius = self.truncated_gaussian(
                        rmin=0.1,
                        rmax=self.randomized_max_radius,
                        rmean=(self.randomized_max_radius + 0.1) / 2,
                        rstd=(self.randomized_max_radius - 0.1) / 4
                    )
                    else:
                        raise ValueError("Unsupported distribution type.")
                else:
                    circle_radius = self.set_circle_radius

                cx = random.uniform(-circle_radius, self.layout_x + circle_radius)
                cy = random.uniform(-circle_radius, self.layout_y + circle_radius)

                potential_positions = [(cx, cy)]

                if cx - circle_radius < 0:
                    potential_positions.append((cx + self.layout_x, cy))
                if cx + circle_radius > self.layout_x:
                    potential_positions.append((cx - self.layout_x, cy))
                if cy - circle_radius < 0:
                    potential_positions.append((cx, cy + self.layout_y))
                if cy + circle_radius > self.layout_y:
                    potential_positions.append((cx, cy - self.layout_y))

                if cx - circle_radius < 0 and cy - circle_radius < 0:
                    potential_positions.append((cx + self.layout_x, cy + self.layout_y))
                if cx + circle_radius > self.layout_x and cy - circle_radius < 0:
                    potential_positions.append((cx - self.layout_x, cy + self.layout_y))
                if cx - circle_radius < 0 and cy + circle_radius > self.layout_y:
                    potential_positions.append((cx + self.layout_x, cy - self.layout_y))
                if cx + circle_radius > self.layout_x and cy + circle_radius > self.layout_y:
                    potential_positions.append((cx - self.layout_x, cy - self.layout_y))

                valid_placement = all(
                    not self.check_circ_overlap(px, py, circle_radius, x, y, r)
                    for px, py in potential_positions
                    for x, y, r in self.placed_circles
                )

            buffer = 0.0001
            if (cx - circle_radius >= buffer and
                cx + circle_radius <= self.layout_x - buffer and
                cy - circle_radius >= buffer and
                cy + circle_radius <= self.layout_y - buffer):
                placed_count += 1
                self.placed_circles.append((cx, cy, circle_radius))
                circle_tags.append(self.add_circle(cx, cy, circle_radius))

                for px, py in potential_positions[1:]:
                    self.placed_circles.append((px, py, circle_radius))
                    circle_tags.append(self.add_circle(px, py, circle_radius))

        gmsh.model.occ.synchronize()
        gmsh.model.occ.intersect([(2, tag) for tag in circle_tags], [(2, rect)], removeTool=False)
        gmsh.model.occ.synchronize()
        gmsh.model.occ.fragment([(2, rect)], [(2, tag) for tag in circle_tags])
        gmsh.model.occ.synchronize()
        edges = gmsh.model.getEntities(dim=1)
        for i, (dim, tag) in enumerate(edges):
            gmsh.model.addPhysicalGroup(dim, [tag], tag=10 + i)
            gmsh.model.setPhysicalName(dim, 10 + i, f"Edge_{i}")

        circle_surfaces = [tag for tag in circle_tags]
        gmsh.model.addPhysicalGroup(2, circle_surfaces, tag=20)
        gmsh.model.setPhysicalName(2, 20, "Circles")

        all_surfaces = gmsh.model.getEntities(dim=2)
        background_surfaces = [s[1] for s in all_surfaces if s[1] not in circle_surfaces]
        gmsh.model.addPhysicalGroup(2, background_surfaces, tag=30)
        gmsh.model.setPhysicalName(2, 30, "Background")

        gmsh.model.mesh.generate(2)

        mesh, cell_tags, facet_tags = gmshio.model_to_mesh(gmsh.model, comm, 0, gdim=2)
        mesh.topology.create_entities(mesh.topology.dim - 1)
        mesh.topology.create_connectivity(mesh.topology.dim - 1, mesh.topology.dim)

        with XDMFFile(comm, save_path, "w") as xdmf:
            xdmf.write_mesh(mesh)
            xdmf.write_meshtags(cell_tags, mesh.geometry)
            xdmf.write_meshtags(facet_tags, mesh.geometry)

        if visualize:
            try:
                gmsh.fltk.run()
            except Exception as e:
                print(f"Visualization failed: {e}")

        gmsh.finalize()