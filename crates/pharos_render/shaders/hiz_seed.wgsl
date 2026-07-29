// Nova3D 39cc44a — HiZ mip-0 compute seed.
//
// The bug: the HiZ (Hierarchical-Z / depth pyramid) build loop assumed
// mip 0 already held raw scene depth and only computed mips 1..N by
// max-pooling parent samples. On cold init (frame 0, resize, or after
// a swapchain reconfigure) mip 0 was undefined, so the whole pyramid
// was junk — SSR reservoir tests and VCR frustum culling then either
// over-culled (dark scene) or under-culled (missed occlusion).
//
// The fix: run a dedicated seed compute pass BEFORE the pyramid
// downsample chain. It reads the depth attachment and writes the
// raw depth (linearised to a comparable scalar) into HiZ mip 0. The
// downsample chain then max-pools from a known-good level.
//
// This pass must run every frame — a stale mip 0 from the previous
// frame is nearly as bad as an uninitialised one when the camera
// moved (fixed-point pyramid entries no longer correspond to the
// current-frame geometry). The dispatch is one thread per HiZ pixel
// (workgroup 8x8; caller sets group counts = ceil(w/8) x ceil(h/8)).

@group(0) @binding(0) var depth_src : texture_depth_2d;
@group(0) @binding(1) var hiz_mip0  : texture_storage_2d<r32float, write>;

// Nova3D 39cc44a — mip-0 seed entry point.
@compute @workgroup_size(8, 8, 1)
fn hiz_seed(@builtin(global_invocation_id) gid : vec3<u32>) {
    let dims = textureDimensions(hiz_mip0);
    if (gid.x >= dims.x || gid.y >= dims.y) {
        return;
    }
    let coord = vec2<i32>(i32(gid.x), i32(gid.y));
    // textureLoad on a depth texture returns the non-linear device depth
    // in [0, 1]. The downsample chain compares samples directly so we
    // do NOT linearise here — same-space comparison keeps the pyramid
    // invariant consistent across mips.
    let z = textureLoad(depth_src, coord, 0);
    textureStore(hiz_mip0, coord, vec4<f32>(z, 0.0, 0.0, 0.0));
}
