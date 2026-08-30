"""Profile SoftBodyRenderer.render() on ~200-node lattice."""
import cProfile
import pstats
import io
import sys

sys.path.insert(0, "H:/Github/SlapPyEngine/python")

import numpy as np
from slappyengine.softbody.world import SoftBodyWorld
from slappyengine.softbody.body_builders import make_lattice_body
from slappyengine.softbody.render import SoftBodyRenderer, SoftBodyRenderConfig
from slappyengine.softbody.solver import step as solver_step

# ~200 nodes: 13x14 lattice = 14*15 = 210 nodes
world = SoftBodyWorld()
b1 = make_lattice_body(world, "muscle", 13, 14, 0.05, position=(-0.3, 0.0), name="lattice")
print(f"Nodes: {world.nodes.count}, beams: {world.beams.count}")

# Step a few times so positions are nontrivial
for _ in range(5):
    solver_step(world)

# Mark some broken beams for realistic rendering
world.beams.broken[::13] = True

cfg = SoftBodyRenderConfig.from_yaml()
r = SoftBodyRenderer(config=cfg)

# Warm up
for _ in range(3):
    r.render(world)

pr = cProfile.Profile()
pr.enable()
for _ in range(50):
    r.render(world)
pr.disable()

s = io.StringIO()
ps = pstats.Stats(pr, stream=s).sort_stats("cumulative")
ps.print_stats(30)
print("=== CUMULATIVE ===")
print(s.getvalue())

s2 = io.StringIO()
ps2 = pstats.Stats(pr, stream=s2).sort_stats("tottime")
ps2.print_stats(25)
print("=== BY TOTTIME ===")
print(s2.getvalue())

import time
N = 30
t0 = time.perf_counter()
for _ in range(N):
    r.render(world)
t1 = time.perf_counter()
print(f"\nSoftBodyRenderer.render() avg time: {(t1-t0)/N*1e3:.2f} ms  (N={N})")
