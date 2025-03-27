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
    gmsh.model.geo.addPoint(0, 0, 0, size, 1)
    gmsh.model.geo.addPoint(layout_x, 0, 0, size, 2)
    gmsh.model.geo.addPoint(layout_x, layout_y, 0, size, 3)
    gmsh.model.geo.addPoint(0, layout_y, 0, size, 4)
    gmsh.model.geo.addLine(1, 2, 1)
    gmsh.model.geo.addLine(2, 3, 2)
    gmsh.model.geo.addLine(3, 4, 3)
    gmsh.model.geo.addLine(4, 1, 4)
    gmsh.model.geo.addCurveLoop([1, 2, 3, 4], 1)
    gmsh.model.geo.addPlaneSurface([1], 1)

# FUNCTION TO ADD A CIRCLE
def add_circle(cx, cy, radius):
    center_tag = gmsh.model.geo.addPoint(cx, cy, 0, size)

    p1 = gmsh.model.geo.addPoint(cx + radius, cy, 0, size)
    p2 = gmsh.model.geo.addPoint(cx, cy + radius, 0, size)
    p3 = gmsh.model.geo.addPoint(cx - radius, cy, 0, size)
    p4 = gmsh.model.geo.addPoint(cx, cy - radius, 0, size)

    arc1 = gmsh.model.geo.addCircleArc(p1, center_tag, p2)
    arc2 = gmsh.model.geo.addCircleArc(p2, center_tag, p3)
    arc3 = gmsh.model.geo.addCircleArc(p3, center_tag, p4)
    arc4 = gmsh.model.geo.addCircleArc(p4, center_tag, p1)

    curve_loop_tag = gmsh.model.geo.addCurveLoop([arc1, arc2, arc3, arc4])
    gmsh.model.geo.addPlaneSurface([curve_loop_tag])

# MAIN
def main():
    gmsh.initialize()
    gmsh.model.add("Mesh Result")
    create_rect()

    for _ in range(circles):
        valid_placement = False
        while not valid_placement:
            circ_x_bound = random.uniform(-circle_radius, layout_x + circle_radius)
            circ_y_bound = random.uniform(-circle_radius, layout_y + circle_radius)

            potential_positions = [
                (circ_x_bound, circ_y_bound),
            ]

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

        add_circle(circ_x_bound, circ_y_bound, circle_radius)

        for px, py in potential_positions[1:]:
            placed_circles.append((px, py, circle_radius))
            add_circle(px, py, circle_radius)

    gmsh.model.geo.synchronize()
    gmsh.model.mesh.generate(2)
    gmsh.fltk.run()
    gmsh.finalize()

if __name__ == "__main__":
    main()