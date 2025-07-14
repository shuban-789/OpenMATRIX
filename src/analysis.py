"""
Run with (rquires fenicsx 0.6.0):
    mpirun -np 1 python analysis.py square_with_circle.msh
"""
import sys
from mpi4py import MPI
import numpy as np
from petsc4py import PETSc
from dolfinx import fem, io
from dolfinx.io import gmshio
import ufl
import csv
import json
import re
import os

comm = MPI.COMM_WORLD
mesh_file = sys.argv[1] if len(sys.argv) > 1 else "square_with_circle.msh"
results_path = sys.argv[2] if len(sys.argv) > 2 else "results.csv"
input_json_path = sys.argv[3] if len(sys.argv) > 3 else "input.json"
create_files = sys.argv[4] if len(sys.argv) > 4 else "0"

# ----------------------------------------------------------------------
# Read mesh & tags from the .msh file generated in Gmsh
# ----------------------------------------------------------------------
# We assume the following physical tags in the .msh file:
# Facets:
#   1 = bottom edge (roller)
#   2 = right edge (roller)
#   3 = top edge (pressure)
#   4 = left edge (roller)
# Cells:
#   1 = inclusion (cell tag)
#   2 = matrix (cell tag)

with io.XDMFFile(comm, mesh_file, "r") as xdmf:
    mesh = xdmf.read_mesh()
    mesh.topology.create_entities(dim=1)
    cell_tags = xdmf.read_meshtags(mesh, name="cell_tags")
    facet_tags = xdmf.read_meshtags(mesh, name="facet_tags")

# ----------------------------------------------------------------------
# Function space and material properties
# ----------------------------------------------------------------------
V = fem.VectorFunctionSpace(mesh, ("CG", 1))

# Isotropic data 
E_LPSCl, nu_LPSCl = 7.8e9, 0.33      # inclusion
E_Si,    nu_Si    = 1.65e11, 0.3    # matrix

def lame(E, nu):
    mu = E / (2.0 * (1.0 + nu))
    lam = E * nu / ((1.0 + nu) * (1.0 - 2.0 * nu))
    return lam, mu

lam1, mu1 = lame(E_LPSCl, nu_LPSCl)
lam2, mu2 = lame(E_Si, nu_Si)

# Create DG0 spaces for lam and mu
DG0 = fem.FunctionSpace(mesh, ("DG", 0))
lam = fem.Function(DG0)
mu = fem.Function(DG0)

# Assign values based on cell_tags
cell_values = cell_tags.values
lam.vector.array[cell_values == 1] = lam1
lam.vector.array[cell_values == 2] = lam2
mu.vector.array[cell_values == 1]  = mu1
mu.vector.array[cell_values == 2]  = mu2
lam.x.scatter_forward()
mu.x.scatter_forward()

# ----------------------------------------------------------------------
# Variational formulation (plane strain)
# ----------------------------------------------------------------------
u, v = ufl.TrialFunction(V), ufl.TestFunction(V)

def eps(u): return ufl.sym(ufl.grad(u))
def sigma(u, lam, mu): return 2*mu*eps(u) + lam*ufl.tr(eps(u))*ufl.Identity(2)

dx = ufl.Measure("dx", domain=mesh, subdomain_data=cell_tags)
ds = ufl.Measure("ds", domain=mesh, subdomain_data=facet_tags)

a = ufl.inner(sigma(u, lam, mu), eps(v))*dx

p_mag = 75.0e6 # Pa, uniform pressure
n = ufl.FacetNormal(mesh) # outward normal
L = ufl.dot(-p_mag * n, v) * ds(3)

# ----------------------------------------------------------------------
# Roller boundary conditions (zero normal displacement)
# ----------------------------------------------------------------------
def dirichlet_on_component(facet_id, comp):
    facets = facet_tags.indices[facet_tags.values == facet_id]
    dofs = fem.locate_dofs_topological(V.sub(comp), mesh.topology.dim - 1, facets)
    zero = fem.Constant(mesh, PETSc.ScalarType(0))
    return fem.dirichletbc(zero, dofs, V.sub(comp))

bcs = [dirichlet_on_component(1, 1),  # bottom fix u_y
       dirichlet_on_component(2, 0),  # right  fix u_x
       dirichlet_on_component(4, 0)]  # left   fix u_x
       

# ----------------------------------------------------------------------
# Solve forward problem
# ----------------------------------------------------------------------
problem = fem.petsc.LinearProblem(
    a, L, bcs=bcs,
    petsc_options={"ksp_type": "cg", "pc_type": "gamg", "ksp_rtol": 1e-8}
)
uh = problem.solve()
uh.name = "displacement"

if create_files == "1":
    with io.XDMFFile(comm, "displacement.xdmf", "w") as out:
        out.write_mesh(mesh)
        out.write_function(uh)

# ----------------------------------------------------------------------
# Compute and save stress
# ----------------------------------------------------------------------
# Compute stress tensor
S = sigma(uh, lam, mu)

# Compute von Mises: sqrt(3/2 * dev(S):dev(S))
d = mesh.geometry.dim
I = ufl.Identity(d)
dev = S - (1.0/3.0)*ufl.tr(S)*I
vms_expr = ufl.sqrt(3.0/2.0 * ufl.inner(dev, dev))

# Project von Mises to DG0
u_vms, v_vms = ufl.TrialFunction(DG0), ufl.TestFunction(DG0)
l_proj = ufl.inner(vms_expr, v_vms)*dx
a_proj = ufl.inner(u_vms, v_vms)*dx
proj_problem = fem.petsc.LinearProblem(
    a_proj, l_proj, 
    petsc_options={"ksp_type": "preonly", "pc_type": "lu"})
vms = proj_problem.solve()
vms.name = "vonMises"

# Write results to XDMF
if create_files == "1":
    with io.XDMFFile(comm, "vonMises.xdmf", "w") as out:
        out.write_mesh(mesh)
        out.write_function(vms)

# Print max von Mises
vms_arr = vms.x.array
max_vms = np.max(vms_arr)
if comm.rank == 0:
    print(f"Max von Mises stress: {max_vms/1e6:.3f} MPa")

# Save results to CSV, read potential analysis inputs from JSON
input_json_file = open(input_json_path, "r")
input_fields = json.load(input_json_file)

mesh_info = open(os.path.join(os.path.dirname(mesh_file), "meshinfo.json"), "r")
mesh_info_data = json.load(mesh_info)

distribution = mesh_info_data["distribution"]
mesh_id = mesh_info_data["id"]
circles = mesh_info_data["circles"]

csv_file = open(results_path + "/data.csv", "a", newline="")
writer = csv.writer(csv_file)
writer.writerow([int(mesh_id), circles, max_vms, distribution])
csv_file.close()
input_json_file.close()