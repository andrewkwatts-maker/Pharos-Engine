"""Profile FluidRenderer.render() on ~140 particles in both modes."""
import cProfile
import pstats
import io
import sys

sys.path.insert(0, "H:/Github/SlapPyEngine/python")

import numpy as np
from slappyengine.fluid.world import FluidWorld
from slappyengine.fluid.render import FluidRenderer, FluidRenderConfig
from slappyengine.fluid.solver import pbf_step

# ~140 particles: 12x12 = 144
world = FluidWorld()
world.add_block_of_particles("water", 12, 12, origin=(-0.4, 0.0))
print(f"Particles: {world.particles.count}")

# Step a few times
for _ in range(5):
    pbf_step(world)

cfg = FluidRenderConfig.from_yaml()
r = FluidRenderer(config=cfg)

# --- Point-splat mode ---
cfg.surface_mode = False
for _ in range(3):
    r.render(world)

pr = cProfile.Profile()
pr.enable()
for _ in range(50):
    r.render(world)
pr.disable()

s = io.StringIO()
ps = pstats.Stats(pr, stream=s).sort_stats("cumulative")
ps.print_stats(25)
print("=== POINT-SPLAT MODE: CUMULATIVE ===")
print(s.getvalue())

s2 = io.StringIO()
ps2 = pstats.Stats(pr, stream=s2).sort_stats("tottime")
ps2.print_stats(20)
print("=== POINT-SPLAT MODE: BY TOTTIME ===")
print(s2.getvalue())

import time
N = 30
t0 = time.perf_counter()
for _ in range(N):
    r.render(world)
t1 = time.perf_counter()
point_time = (t1-t0)/N*1e3
print(f"\nFluidRenderer point-splat avg: {point_time:.2f} ms  (N={N})")

# --- Surface mode ---
cfg.surface_mode = True
for _ in range(3):
    r.render(world)

pr2 = cProfile.Profile()
pr2.enable()
for _ in range(30):
    r.render(world)
pr2.disable()

s3 = io.StringIO()
ps3 = pstats.Stats(pr2, stream=s3).sort_stats("cumulative")
ps3.print_stats(25)
print("=== SURFACE MODE: CUMULATIVE ===")
print(s3.getvalue())

s4 = io.StringIO()
ps4 = pstats.Stats(pr2, stream=s4).sort_stats("tottime")
ps4.print_stats(20)
print("=== SURFACE MODE: BY TOTTIME ===")
print(s4.getvalue())

t0 = time.perf_counter()
for _ in range(N):
    r.render(world)
t1 = time.perf_counter()
surf_time = (t1-t0)/N*1e3
print(f"\nFluidRenderer surface-mode avg: {surf_time:.2f} ms  (N={N})")
print(f"Surface vs point: {surf_time/point_time:.1f}x")
