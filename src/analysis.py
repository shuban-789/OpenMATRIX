"""
Run with (requires fenicsx 0.6.0):
    mpirun -np 1 python analysis.py mesh3.xdmf
"""

import sys
import os
import re
from mpi4py import MPI
from petsc4py import PETSc
from dolfinx import fem, io
from dolfinx.io import gmshio
from dolfinx.io import XDMFFile
import ufl

# --------------------------------------------------
# Setup & mesh import
# --------------------------------------------------
comm = MPI.COMM_WORLD
mesh_file = sys.argv[1] if len(sys.argv) > 1 else "square_with_circle.msh"

with XDMFFile(comm, mesh_file, "r") as xdmf:
    mesh = xdmf.read_mesh()
    mesh.topology.create_entities(dim=1)
    cell_tags = xdmf.read_meshtags(mesh, name="cell_tags")
    facet_tags = xdmf.read_meshtags(mesh, name="facet_tags")


# --------------------------------------------------
# Function space and material properties
# --------------------------------------------------
V = fem.VectorFunctionSpace(mesh, ("CG", 1))

E_LPSCl, nu_LPSCl = 7.8e9, 0.33   # inclusion
E_Si,    nu_Si    = 1.65e11, 0.3  # matrix

def lame(E, nu):
    mu = E / (2.0 * (1.0 + nu))
    lam = E * nu / ((1.0 + nu) * (1.0 - 2.0 * nu))
    return lam, mu

lam1, mu1 = lame(E_LPSCl, nu_LPSCl)
lam2, mu2 = lame(E_Si, nu_Si)

# --------------------------------------------------
# Variational formulation (plane strain)
# --------------------------------------------------
u, v = ufl.TrialFunction(V), ufl.TestFunction(V)

def eps(u): return ufl.sym(ufl.grad(u))
def sigma(u, lam, mu): return 2*mu*eps(u) + lam*ufl.tr(eps(u))*ufl.Identity(2)

dx = ufl.Measure("dx", domain=mesh, subdomain_data=cell_tags)
ds = ufl.Measure("ds", domain=mesh, subdomain_data=facet_tags)

a = ufl.inner(sigma(u, lam1, mu1), eps(v)) * dx(1) + \
    ufl.inner(sigma(u, lam2, mu2), eps(v)) * dx(2)

p_mag = 75.0e6  # Pa, uniform pressure
n = ufl.FacetNormal(mesh)
L = ufl.dot(-p_mag * n, v) * ds(4)

# --------------------------------------------------
# Roller boundary conditions
# --------------------------------------------------
def dirichlet_on_component(facet_id, comp):
    facets = facet_tags.indices[facet_tags.values == facet_id]
    dofs = fem.locate_dofs_topological(V.sub(comp), mesh.topology.dim - 1, facets)
    zero = fem.Constant(mesh, PETSc.ScalarType(0))
    return fem.dirichletbc(zero, dofs, V.sub(comp))

bcs = [
    dirichlet_on_component(1, 0),  # left fix u_x
    dirichlet_on_component(2, 1),  # bottom fix u_y
    dirichlet_on_component(3, 0)   # right fix u_x
]

# --------------------------------------------------
# Solve problem
# --------------------------------------------------
problem = fem.petsc.LinearProblem(
    a, L, bcs=bcs,
    petsc_options={"ksp_type": "cg", "pc_type": "gamg", "ksp_rtol": 1e-8}
)
uh = problem.solve()
uh.name = "displacement"

# --------------------------------------------------
# Export result to same directory with dynamic name
# --------------------------------------------------
mesh_basename = os.path.basename(mesh_file)
match = re.search(r'mesh(\d+)', mesh_basename)
mesh_id = match.group(1) if match else "unknown"

result_filename = f"result{mesh_id}.xdmf"
result_path = os.path.join(os.path.dirname(mesh_file), result_filename)

with io.XDMFFile(comm, result_path, "w") as out:
    out.write_mesh(mesh)
    out.write_function(uh)

print(f"Analysis complete, {result_path}")
