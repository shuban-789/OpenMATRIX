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
    d = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
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

# MAIN
def main():
    gmsh.initialize()
    gmsh.model.add("Mesh Result")
    create_rect()

    next_available_tag = 5

    for _ in range(circles):
        valid_placement = False
        while not valid_placement:
            circ_x_bound = random.uniform(circle_radius, layout_x - circle_radius)
            circ_y_bound = random.uniform(circle_radius, layout_y - circle_radius)

            valid_placement = all(
                not check_circ_overlap(circ_x_bound, circ_y_bound, circle_radius, x, y, r)
                for x, y, r in placed_circles
            )

        placed_circles.append((circ_x_bound, circ_y_bound, circle_radius))

        center_tag = next_available_tag
        gmsh.model.geo.addPoint(circ_x_bound, circ_y_bound, 0, size, center_tag)

        start_tag = center_tag + 1
        end_tag = center_tag + 2
        gmsh.model.geo.addPoint(circ_x_bound + circle_radius, circ_y_bound, 0, size, start_tag)
        gmsh.model.geo.addPoint(circ_x_bound - circle_radius, circ_y_bound, 0, size, end_tag)

        gmsh.model.geo.addCircleArc(start_tag, center_tag, end_tag, center_tag + 3)
        gmsh.model.geo.addCircleArc(end_tag, center_tag, start_tag, center_tag + 4)

        next_available_tag += 5

    gmsh.model.geo.synchronize()
    gmsh.model.mesh.generate(2)
    gmsh.fltk.run()
    gmsh.finalize()


if __name__ == "__main__":
    main()
