#!/usr/bin/python3
import gmsh
import random
import math

# VARIABLES
layout = "4x4"
layout_x = int(layout[0])
layout_y = int(layout[2])
size = 0.01
circles = 5
circle_radius = 0.5

# STORED CIRCLE DATA
placed_circles = []

# HELPER FUNCTIONS
def check_circ_overlap(x1, y1, r1, x2, y2, r2) -> bool:
    d = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
    return d < (r1 + r2)

def create_rect():
    return gmsh.model.occ.addRectangle(0, 0, 0, layout_x, layout_y)

# FUNCTION TO ADD A CIRCLE
def add_circle(cx, cy, radius):
    return gmsh.model.occ.addDisk(cx, cy, 0, radius, radius)

# MAIN
def main():
    gmsh.initialize()
    gmsh.model.add("Mesh Result")
    
    rect = create_rect()
    circle_tags = []

    for _ in range(circles):
        valid_placement = False
        while not valid_placement:
            circ_x_bound = random.uniform(-circle_radius, layout_x + circle_radius)
            circ_y_bound = random.uniform(-circle_radius, layout_y + circle_radius)

            potential_positions = [(circ_x_bound, circ_y_bound)]
            if circ_x_bound - circle_radius < 0:
                potential_positions.append((circ_x_bound + layout_x, circ_y_bound))
            if circ_x_bound + circle_radius > layout_x:
                potential_positions.append((circ_x_bound - layout_x, circ_y_bound))
            if circ_y_bound - circle_radius < 0:
                potential_positions.append((circ_x_bound, circ_y_bound + layout_y))
            if circ_y_bound + circle_radius > layout_y:
                potential_positions.append((circ_x_bound, circ_y_bound - layout_y))
            if (circ_x_bound - circle_radius < 0 and circ_y_bound - circle_radius < 0):
                potential_positions.append((circ_x_bound + layout_x, circ_y_bound + layout_y))
            if (circ_x_bound + circle_radius > layout_x and circ_y_bound - circle_radius < 0):
                potential_positions.append((circ_x_bound - layout_x, circ_y_bound + layout_y))
            if (circ_x_bound - circle_radius < 0 and circ_y_bound + circle_radius > layout_y):
                potential_positions.append((circ_x_bound + layout_x, circ_y_bound - layout_y))
            if (circ_x_bound + circle_radius > layout_x and circ_y_bound + circle_radius > layout_y):
                potential_positions.append((circ_x_bound - layout_x, circ_y_bound - layout_y))

            valid_placement = all(
                not check_circ_overlap(px, py, circle_radius, x, y, r)
                for px, py in potential_positions
                for x, y, r in placed_circles
            )

        placed_circles.append((circ_x_bound, circ_y_bound, circle_radius))
        circle_tags.append(add_circle(circ_x_bound, circ_y_bound, circle_radius))

        for px, py in potential_positions[1:]:
            placed_circles.append((px, py, circle_radius))
            circle_tags.append(add_circle(px, py, circle_radius))
    
    gmsh.model.occ.synchronize()
    
    gmsh.model.occ.intersect([(2, tag) for tag in circle_tags], [(2, rect)], removeTool=False)
    gmsh.model.occ.synchronize()
    
    gmsh.model.occ.fragment([(2, rect)], [(2, tag) for tag in circle_tags])
    gmsh.model.occ.synchronize()
    
    gmsh.model.mesh.generate(2)
    gmsh.fltk.run()
    gmsh.finalize()

if __name__ == "__main__":
    main()
