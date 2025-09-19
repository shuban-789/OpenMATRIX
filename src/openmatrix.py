#!/usr/bin/python3
from mpi4py import MPI
from dolfinx.io import gmshio, XDMFFile
from scipy.stats import truncnorm
from rich.progress import Progress
from rich.console import Console
import gmsh
import random
import math
import json
import os
import re

console = Console()

class MeshGenerator:
    def __init__(self, layout, size, circles, randomized_max_radius, circ_distribution_type,
                 set_circle_radius, mesh_element_size, randomized_radius, min_fraction_inside=0, circ_af=None):
        self.layout = layout
        self.layout_x = float(layout[0])
        self.layout_y = float(layout[1])
        self.size = size
        self.circles = circles
        self.randomized_max_radius = randomized_max_radius
        self.circ_distribution_type = circ_distribution_type
        self.set_circle_radius = set_circle_radius
        self.mesh_element_size = mesh_element_size
        self.randomized_radius = randomized_radius
        self.placed_circles = []
        self.min_fraction_inside = min_fraction_inside
        self.circle_area_sum = 0.0
        self.square_area_sum = self.layout_x * self.layout_y
        self.use_ratio = circ_af[0]
        self.percentage = circ_af[1]
        self.error_bound = circ_af[2]

    def check_circ_overlap(self, x1, y1, r1, x2, y2, r2) -> bool:
        d = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
        return d < (r1 + r2)

    def is_enough_inside(self, cx, cy, radius):
        x_min = cx - radius
        x_max = cx + radius
        y_min = cy - radius
        y_max = cy + radius

        x_overlap = max(0, min(x_max, self.layout_x) - max(x_min, 0))
        y_overlap = max(0, min(y_max, self.layout_y) - max(y_min, 0))

        overlap_area = x_overlap * y_overlap
        circle_area = math.pi * radius * radius

        return overlap_area / circle_area >= self.min_fraction_inside

    def create_rect(self):
        rect = gmsh.model.occ.addRectangle(0, 0, 0, self.layout_x, self.layout_y)
        gmsh.model.occ.synchronize()
        rect_edges = gmsh.model.getBoundary([(2, rect)], oriented=True)
        return rect, rect_edges

    def add_circle(self, cx, cy, radius):
        return gmsh.model.occ.addDisk(cx, cy, 0, radius, radius)

    def truncated_gaussian(self, rmin, rmax, rmean, rstd):
        a, b = (rmin - rmean) / rstd, (rmax - rmean) / rstd
        return truncnorm.rvs(a, b, loc=rmean, scale=rstd)

    def generate_from_af(self, visualize=True, save_path=None):
        comm = MPI.COMM_WORLD
        rank = comm.rank

        gmsh.initialize()
        gmsh.model.add("Mesh Result")
        gmsh.option.setNumber("Mesh.CharacteristicLengthMax", self.mesh_element_size)
        gmsh.option.setNumber("General.Terminal", 0)

        rect, rect_edges = self.create_rect()
        circle_tags = []

        placed_count = 0
        max_attempts = 10000
        attempts = 0

        target_ratio = self.percentage
        lower_bound = (target_ratio - self.error_bound) / 100.0 * self.square_area_sum
        upper_bound = (target_ratio + self.error_bound) / 100.0 * self.square_area_sum

        with Progress() as progress:
            task = progress.add_task(
                f"[cyan]Generating mesh",
                total=upper_bound,
            )
            while True:
                if lower_bound <= self.circle_area_sum <= upper_bound:
                    break
                if attempts > max_attempts:
                    console.log(f"[red]Max attempts ({max_attempts}) exhausted.[/red]")
                    break
                attempts += 1

                valid_placement = False
                while not valid_placement:
                    if self.randomized_radius:
                        if self.circ_distribution_type == "uniform":
                            circle_radius = random.uniform(0.1, self.randomized_max_radius)
                        elif self.circ_distribution_type == "gaussian":
                            circle_radius = self.truncated_gaussian(
                                rmin=0.1,
                                rmax=self.randomized_max_radius,
                                rmean=(self.randomized_max_radius + 0.1) / 2,
                                rstd=(self.randomized_max_radius - 0.1) / 4
                            )
                        else:
                            raise ValueError("Unsupported distribution type.")
                    else:
                        raise ValueError("Must have randomized radius enabled. Unrandomized is only for set circles")

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
                    ) and self.is_enough_inside(cx, cy, circle_radius)

                new_area = math.pi * circle_radius ** 2
                
                self.placed_circles.append((cx, cy, circle_radius))
                circle_tags.append(self.add_circle(cx, cy, circle_radius))
                
                for px, py in potential_positions[1:]:
                    self.placed_circles.append((px, py, circle_radius))
                    circle_tags.append(self.add_circle(px, py, circle_radius))
                
                self.circle_area_sum += new_area
                placed_count += 1

                if self.circle_area_sum > upper_bound:
                    for _ in potential_positions:
                        self.placed_circles.pop()
                        tag = circle_tags.pop()
                        gmsh.model.occ.remove([(2, tag)], recursive=True)
                    self.circle_area_sum -= new_area
                    placed_count -= 1
                else:
                    progress.update(task, completed=self.circle_area_sum)

        gmsh.model.occ.synchronize()

        valid_circle_tags = []
        for tag in circle_tags:
            try:
                gmsh.model.occ.getCenterOfMass(2, tag)
                valid_circle_tags.append(tag)
            except:
                pass

        rect_tag = [(2, rect)]
        circle_entities = [(2, tag) for tag in valid_circle_tags]
        
        if circle_entities:
            out_dimtags, _ = gmsh.model.occ.fragment(rect_tag, circle_entities)
            gmsh.model.occ.synchronize()
            
            all_surfaces_after_fragment = gmsh.model.getEntities(dim=2)
            for dim, surf_tag in all_surfaces_after_fragment:
                try:
                    surf_center = gmsh.model.occ.getCenterOfMass(2, surf_tag)
                    surf_x, surf_y = surf_center[0], surf_center[1]
                    
                    if not (0 <= surf_x <= self.layout_x and 0 <= surf_y <= self.layout_y):
                        gmsh.model.occ.remove([(2, surf_tag)], recursive=True)
                except:
                    continue
            
            gmsh.model.occ.synchronize()

        all_surfaces = gmsh.model.getEntities(dim=2)
        circle_surfaces = []

        for dim, surf_tag in all_surfaces:
            try:
                surf_center = gmsh.model.occ.getCenterOfMass(2, surf_tag)
                surf_x, surf_y = surf_center[0], surf_center[1]
                for cx, cy, r in self.placed_circles:
                    distance = math.sqrt((surf_x - cx)**2 + (surf_y - cy)**2)
                    if distance <= r + 1e-6 and 0 <= surf_x <= self.layout_x and 0 <= surf_y <= self.layout_y:
                        circle_surfaces.append(surf_tag)
                        break
            except:
                continue

        all_surface_tags = [surf_tag for dim, surf_tag in all_surfaces]
        
        background_surfaces = [tag for tag in all_surface_tags if tag not in circle_surfaces]


        console.log(f"[green]Total surfaces: {len(all_surface_tags)}[/green]")
        console.log(f"[green]Circle surfaces: {len(circle_surfaces)}[/green]")
        console.log(f"[green]Background surfaces: {len(background_surfaces)}[/green]")

        all_edges = gmsh.model.getEntities(dim=1)
        def midpoint(tag):
            x, y, _ = gmsh.model.occ.getCenterOfMass(1, tag)
            return x, y
        tol = 1e-6
        left, right, bottom, top = [], [], [], []
        for dim, tag in all_edges:
            x, y = midpoint(tag)
            if abs(x - 0) < tol:
                left.append(tag)
            elif abs(x - self.layout_x) < tol:
                right.append(tag)
            elif abs(y - 0) < tol:
                bottom.append(tag)
            elif abs(y - self.layout_y) < tol:
                top.append(tag)

        gmsh.model.addPhysicalGroup(1, bottom, tag=1)
        gmsh.model.setPhysicalName(1, 1, "Bottom")
        gmsh.model.addPhysicalGroup(1, right, tag=2)
        gmsh.model.setPhysicalName(1, 2, "Right")
        gmsh.model.addPhysicalGroup(1, top, tag=3)
        gmsh.model.setPhysicalName(1, 3, "Top")
        gmsh.model.addPhysicalGroup(1, left, tag=4)
        gmsh.model.setPhysicalName(1, 4, "Left")

        if circle_surfaces:
            gmsh.model.addPhysicalGroup(2, circle_surfaces, tag=1)
            gmsh.model.setPhysicalName(2, 1, "Circles")
        
        if background_surfaces:
            gmsh.model.addPhysicalGroup(2, background_surfaces, tag=2)
            gmsh.model.setPhysicalName(2, 2, "Background")
        else:
            console.log("[red]WARNING: No background surfaces found![/red]")

        gmsh.model.mesh.generate(2)

        mesh, cell_tags, facet_tags, *rest = gmshio.model_to_mesh(gmsh.model, comm, 0, gdim=2)
        mesh.topology.create_entities(mesh.topology.dim - 1)
        mesh.topology.create_connectivity(mesh.topology.dim - 1, mesh.topology.dim)

        cell_tags.name = "cell_tags"
        facet_tags.name = "facet_tags"

        with XDMFFile(comm, save_path, "w") as xdmf:
            xdmf.write_mesh(mesh)
            xdmf.write_meshtags(cell_tags, mesh.geometry)
            xdmf.write_meshtags(facet_tags, mesh.geometry)

        frac = (self.circle_area_sum / self.square_area_sum) * 100
        size = self.layout_x * self.layout_y

        match = re.search(r'mesh(\d+)\.xdmf$', str(save_path))
        if match:
            n = int(match.group(1))
        else:
            console.log("[red]No match found for save path.[/red]")
            n = 0

        data = {
            "id": n,
            "circles": placed_count,
            "area_fraction": frac,
            "size": size
        }

        save_dir = os.path.dirname(save_path)
        json_path = os.path.join(save_dir, "meshinfo.json")
        json.dump(data, open(json_path, "w"))

        if visualize:
            try:
                gmsh.fltk.run()
            except:
                pass

        gmsh.finalize()

    def generate_from_circles(self, visualize=True, save_path=None):
        comm = MPI.COMM_WORLD
        rank = comm.rank

        gmsh.initialize()
        gmsh.model.add("Mesh Result")
        gmsh.option.setNumber("Mesh.CharacteristicLengthMax", self.mesh_element_size)
        gmsh.option.setNumber("Mesh.Algorithm", 6)
        gmsh.option.setNumber("Mesh.ElementOrder", 1)
        gmsh.option.setNumber("Mesh.SaveAll", 0)
        gmsh.option.setNumber("Mesh.SurfaceFaces", 1)
        gmsh.option.setNumber("General.Terminal", 0)

        rect, rect_edges = self.create_rect()
        circle_tags = []

        placed_count = 0
        max_attempts = 10000
        attempts = 0

        target_ratio = self.percentage
        lower_bound = (target_ratio - self.error_bound) / 100.0 * self.square_area_sum
        upper_bound = (target_ratio + self.error_bound) / 100.0 * self.square_area_sum

        while True:
            if not self.use_ratio and placed_count >= self.circles:
                break
            if self.use_ratio and lower_bound <= self.circle_area_sum <= upper_bound:
                break
            if attempts > max_attempts:
                console.log(f"[red]Max attempts ({max_attempts}) exhausted.[/red]")
                break
            attempts += 1

            valid_placement = False
            while not valid_placement:
                if self.randomized_radius:
                    if self.circ_distribution_type == "uniform":
                        circle_radius = random.uniform(0.1, self.randomized_max_radius)
                    elif self.circ_distribution_type == "gaussian":
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

                cx = random.uniform(-self.randomized_max_radius * 1.5, self.layout_x + self.randomized_max_radius * 1.5)
                cy = random.uniform(-self.randomized_max_radius * 1.5, self.layout_y + self.randomized_max_radius * 1.5)

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
                ) and self.is_enough_inside(cx, cy, circle_radius)

            new_area = math.pi * circle_radius ** 2
            self.placed_circles.append((cx, cy, circle_radius))
            circle = gmsh.model.occ.addDisk(cx, cy, 0, circle_radius, circle_radius)
            circle_tags.append(circle)
            for px, py in potential_positions[1:]:
                self.placed_circles.append((px, py, circle_radius))
                circle = gmsh.model.occ.addDisk(px, py, 0, circle_radius, circle_radius)
                circle_tags.append(circle)
            self.circle_area_sum += new_area
            placed_count += 1

            if self.use_ratio and self.circle_area_sum > upper_bound:
                for _ in potential_positions:
                    self.placed_circles.pop()
                    tag = circle_tags.pop()
                    gmsh.model.occ.remove([(2, tag)], recursive=True)
                self.circle_area_sum -= new_area
                placed_count -= 1

        console.log(f"[green]Placed {placed_count} circles with tags: {circle_tags}[/green]")
        gmsh.model.occ.synchronize()

        status, fragments = gmsh.model.occ.fragment([(2, rect)], [(2, tag) for tag in circle_tags])
        gmsh.model.occ.synchronize()

        all_surfaces = gmsh.model.getEntities(dim=2)
        to_remove = []
        for dim, tag in all_surfaces:
            try:
                cx, cy, _ = gmsh.model.occ.getCenterOfMass(2, tag)
                if not (0 <= cx <= self.layout_x and 0 <= cy <= self.layout_y):
                    to_remove.append((dim, tag))
            except Exception:
                continue
        for ent in to_remove:
            gmsh.model.occ.remove([ent], recursive=True)
        gmsh.model.occ.synchronize()

        all_surfaces = gmsh.model.getEntities(dim=2)
        circle_surfaces = []
        for dim, tag in all_surfaces:
            if tag in circle_tags:
                circle_surfaces.append(tag)
            else:
                try:
                    cx, cy, _ = gmsh.model.occ.getCenterOfMass(2, tag)
                    for pcx, pcy, r in self.placed_circles:
                        dist = math.hypot(cx - pcx, cy - pcy)
                        if dist < r + 1e-6:
                            circle_surfaces.append(tag)
                            break
                except Exception:
                    continue

        circle_surfaces = list(set(circle_surfaces))
        background_surfaces = [s[1] for s in all_surfaces if s[1] not in circle_surfaces]

        console.log(f"[green]Circle surfaces after fragmentation: {circle_surfaces}[/green]")
        console.log(f"[green]Background surfaces: {background_surfaces}[/green]")

        all_edges = gmsh.model.getEntities(dim=1)

        def midpoint(tag):
            x, y, _ = gmsh.model.occ.getCenterOfMass(1, tag)
            return x, y

        tol = 1e-6
        left, right, bottom, top = [], [], [], []

        for dim, tag in all_edges:
            x, y = midpoint(tag)
            if abs(x - 0) < tol:
                left.append(tag)
            elif abs(x - self.layout_x) < tol:
                right.append(tag)
            elif abs(y - 0) < tol:
                bottom.append(tag)
            elif abs(y - self.layout_y) < tol:
                top.append(tag)

        gmsh.model.addPhysicalGroup(1, bottom, tag=1)
        gmsh.model.setPhysicalName(1, 1, "Bottom")
        gmsh.model.addPhysicalGroup(1, right, tag=2)
        gmsh.model.setPhysicalName(1, 2, "Right")
        gmsh.model.addPhysicalGroup(1, top, tag=3)
        gmsh.model.setPhysicalName(1, 3, "Top")
        gmsh.model.addPhysicalGroup(1, left, tag=4)
        gmsh.model.setPhysicalName(1, 4, "Left")

        if circle_surfaces:
            gmsh.model.addPhysicalGroup(2, circle_surfaces, tag=1)
            gmsh.model.setPhysicalName(2, 1, "Circles")
        if background_surfaces:
            gmsh.model.addPhysicalGroup(2, background_surfaces, tag=2)
            gmsh.model.setPhysicalName(2, 2, "Background")

        gmsh.model.mesh.generate(2)

        mesh, cell_tags, facet_tags, *rest = gmshio.model_to_mesh(gmsh.model, comm, 0, gdim=2)
        mesh.topology.create_entities(mesh.topology.dim - 1)
        mesh.topology.create_connectivity(mesh.topology.dim - 1, mesh.topology.dim)

        cell_tags.name = "cell_tags"
        facet_tags.name = "facet_tags"

        with XDMFFile(comm, save_path, "w") as xdmf:
            xdmf.write_mesh(mesh)
            xdmf.write_meshtags(cell_tags)
            xdmf.write_meshtags(facet_tags)

        frac = (self.circle_area_sum / self.square_area_sum) * 100
        size = self.layout_x * self.layout_y

        match = re.search(r'mesh(\d+)\.xdmf$', save_path)
        if match:
            n = int(match.group(1))
        else:
            console.log("[red]No match found.[/red]")

        data = {
            "id": n,
            "circles": placed_count,
            "area_fraction": frac,
            "size": size
        }

        save_dir = os.path.dirname(save_path)
        json_path = os.path.join(save_dir, "meshinfo.json")
        json.dump(data, open(json_path, "w"))

        if visualize:
            try:
                gmsh.fltk.run()
            except:
                pass

        gmsh.finalize()

    def generate(self, visualize, save_path):
        if self.use_ratio:
            self.generate_from_af(visualize, save_path)
        else:
            self.generate_from_circles(visualize, save_path)