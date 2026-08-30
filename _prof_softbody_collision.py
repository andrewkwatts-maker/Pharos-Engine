"""Profile softbody build_contact_pairs hot path."""
import cProfile
import pstats
import io
import sys

sys.path.insert(0, "H:/Github/SlapPyEngine/python")

import numpy as np
from slappyengine.softbody.world import SoftBodyWorld
from slappyengine.softbody.body_builders import make_lattice_body
from slappyengine.softbody.collision import build_contact_pairs, _contact_params

# Build a scene with two stacked lattices (~200 nodes total) so contacts trigger
world = SoftBodyWorld()
# 8x8 lattice = 81 nodes, two of them = 162 nodes; plus ~80 above
b1 = make_lattice_body(world, "muscle", 8, 8, 0.1, position=(-0.5, 0.5), name="lower")
b2 = make_lattice_body(world, "muscle", 8, 8, 0.1, position=(-0.5, -0.4), name="upper")
b3 = make_lattice_body(world, "muscle", 5, 5, 0.1, position=(0.0, -1.5), name="ball")

# Slightly perturb so they're not perfectly aligned
rng = np.random.default_rng(42)
world.nodes.pos += rng.standard_normal(world.nodes.pos.shape).astype(np.float32) * 0.01

print(f"Total nodes: {world.nodes.count}, beams: {world.beams.count}")

params = _contact_params(world)

# Warm up
for _ in range(3):
    build_contact_pairs(world, params)

# Profile
pr = cProfile.Profile()
pr.enable()
for _ in range(200):
    build_contact_pairs(world, params)
pr.disable()

s = io.StringIO()
ps = pstats.Stats(pr, stream=s).sort_stats("cumulative")
ps.print_stats(25)
print(s.getvalue())

# Now profile by tottime to find self-time hotspots
s2 = io.StringIO()
ps2 = pstats.Stats(pr, stream=s2).sort_stats("tottime")
ps2.print_stats(20)
print("=== BY TOTTIME ===")
print(s2.getvalue())

# Timing comparison: total wall time
import time
N = 500
t0 = time.perf_counter()
for _ in range(N):
    build_contact_pairs(world, params)
t1 = time.perf_counter()
print(f"\nbuild_contact_pairs avg time: {(t1-t0)/N*1e6:.1f} us  (N={N})")
