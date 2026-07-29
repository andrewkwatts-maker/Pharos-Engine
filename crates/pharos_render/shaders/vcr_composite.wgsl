// pharos_render :: VCR Stage 4 — Composite.
//
// Fullscreen post-pass. Reads all K reservoir slots per pixel, evaluates
// each sub-camera's cone (mipped environment lookup with SSR fallback),
// sums via WRS weights, applies Beer-Lambert absorption, and blends
// over the primary G-buffer shading result.
//
// Output goes to the final HDR framebuffer that the tone-mapping /
// bloom chain consumes.

@group(0) @binding(0) var g_base_metal:  texture_2d<f32>;
@group(0) @binding(1) var g_normal_rough: texture_2d<f32>;
@group(0) @binding(2) var g_pos_matid:   texture_2d<f32>;
@group(0) @binding(3) var g_ior_absorb:  texture_2d<f32>;
@group(1) @binding(0) var reservoir:     texture_storage_3d<rgba32float, read>;
@group(2) @binding(0) var env_cube:      texture_cube<f32>;
@group(2) @binding(1) var env_sampler:   sampler;
// Sprint 1 Nova3D bug intake: SSR fallback halo fix. When SSR bind
// group is unbound / no reflection input is present, sample the
// lit-colour target (previous forward pass output) instead of black.
// Nova3D shipped a plain vec3(0.0) fallback and that produced dark
// halos around transparent silhouettes when SSR was disabled.
@group(3) @binding(0) var lit_colour:    texture_2d<f32>;
@group(3) @binding(1) var lit_sampler:   sampler;

// Sprint 1 Nova3D bug intake: caustic-emitter Gaussian 2x + 4x.
// Nova3D 0c0c890 — the caustic reservoir contribution was previously
// accumulated with a flat weight, producing hot single-pixel specks
// wherever a caustic emitter's cone hit the primary surface. The fix
// applies a 2D Gaussian falloff at 2x the horizontal reservoir spread
// and 4x the vertical spread (matches the anisotropic footprint of a
// refracted light cone against a flat receiver at grazing angles),
// which spreads the emitter's energy across neighbouring texels and
// eliminates the specks without darkening the average brightness.
const CAUSTIC_GAUSS_SIGMA_X: f32 = 2.0; // Nova3D 0c0c890 — horizontal spread multiplier.
const CAUSTIC_GAUSS_SIGMA_Y: f32 = 4.0; // Nova3D 0c0c890 — vertical spread multiplier.
const CAUSTIC_MATID_MIN: f32 = 1.5;    // slot_matid >= 1.5 => caustic emitter (spec + refr = 0/1).

// Anisotropic Gaussian weight for a caustic reservoir slot at offset
// (dx, dy) from the receiver pixel, using the sigmas above. Kept as a
// helper so the sigmas cannot silently drift out of sync with the
// regression test that locks them.
fn caustic_gaussian_weight(dx: f32, dy: f32) -> f32 {
    let sx = CAUSTIC_GAUSS_SIGMA_X;
    let sy = CAUSTIC_GAUSS_SIGMA_Y;
    let ex = -0.5 * (dx * dx) / (sx * sx);
    let ey = -0.5 * (dy * dy) / (sy * sy);
    return exp(ex + ey);
}

struct VertexOut {
    @builtin(position) clip: vec4<f32>,
    @location(0) uv: vec2<f32>,
};

@vertex
fn vs_fullscreen(@builtin(vertex_index) vid: u32) -> VertexOut {
    // Trick: 3-vert fullscreen triangle covers [-1,1] via clamped uv.
    var v: VertexOut;
    let x = f32((vid << 1u) & 2u) * 2.0 - 1.0;
    let y = f32(vid & 2u) * 2.0 - 1.0;
    v.clip = vec4<f32>(x, y, 0.0, 1.0);
    v.uv = vec2<f32>((x + 1.0) * 0.5, 1.0 - (y + 1.0) * 0.5);
    return v;
}

@fragment
fn fs_main(in: VertexOut) -> @location(0) vec4<f32> {
    let px = vec2<i32>(in.clip.xy);
    let dims = textureDimensions(g_base_metal);
    if (px.x >= i32(dims.x) || px.y >= i32(dims.y)) { return vec4<f32>(0.0); }

    let base = textureLoad(g_base_metal, px, 0);
    let base_colour = base.rgb;
    let metallic = base.a;
    let normal_rough = textureLoad(g_normal_rough, px, 0);
    let normal = normalize(normal_rough.xyz);
    let roughness = normal_rough.a;
    let ior_absorb = textureLoad(g_ior_absorb, px, 0);
    let absorption = ior_absorb.yzw;

    var reflected_sum = vec3<f32>(0.0);
    var refracted_sum = vec3<f32>(0.0);
    var caustic_sum   = vec3<f32>(0.0);
    var total_weight  = 0.0;
    var caustic_weight_sum = 0.0;
    // Sprint 1 fallback source: sample the lit-colour target for the
    // current pixel. Used only when the reservoir has no reflection
    // contribution — avoids Nova3D's dark-halo bug.
    let uvf = vec2<f32>(f32(px.x) + 0.5, f32(px.y) + 0.5)
        / vec2<f32>(f32(dims.x), f32(dims.y));
    let ssr_fallback = textureSampleLevel(lit_colour, lit_sampler, uvf, 0.0).rgb;

    for (var k: u32 = 0u; k < VCR_K_SLOTS; k = k + 1u) {
        let lo = textureLoad(reservoir, vec3<i32>(px, i32(k * 2u)));
        let hi = textureLoad(reservoir, vec3<i32>(px, i32(k * 2u + 1u)));
        let slot_dir = hi.xyz;
        let slot_cone = hi.w;
        let slot_matid = lo.w;
        // Sample env cube with LoD proportional to cone half-angle.
        let lod = slot_cone * 6.0;
        let env = textureSampleLevel(env_cube, env_sampler, slot_dir, lod).rgb;
        let weight = 1.0 / (1.0 + f32(k));    // Sprint 7 replaces with true WRS weight
        // Slot matid: <0.5 = specular, 0.5..1.5 = refraction, >=1.5 = caustic emitter.
        if (slot_matid < 0.5) {
            reflected_sum = reflected_sum + env * weight;
            total_weight = total_weight + weight;
        } else if (slot_matid < CAUSTIC_MATID_MIN) {
            refracted_sum = refracted_sum + env * weight;
            total_weight = total_weight + weight;
        } else {
            // Nova3D 0c0c890 caustic-emitter path: apply the anisotropic
            // Gaussian falloff instead of a flat per-slot weight. slot_dir
            // encodes the emitter-cone direction; project the pixel-space
            // offset from cone axis onto (dx, dy) via the sub-camera basis
            // stored in lo.xyz (Sprint 7 will hydrate this properly; for
            // now use lo.xy directly as the offset).
            let dx = lo.x;
            let dy = lo.y;
            let g = caustic_gaussian_weight(dx, dy) * weight;
            caustic_sum = caustic_sum + env * g;
            caustic_weight_sum = caustic_weight_sum + g;
        }
    }
    if (total_weight > 0.0) {
        reflected_sum = reflected_sum / total_weight;
        refracted_sum = refracted_sum / total_weight;
    } else {
        // No reflection contribution — fall back to lit-colour target
        // instead of leaving the accumulator at zero. Fixes Sprint 1
        // Nova3D SSR-disabled halo bug.
        reflected_sum = ssr_fallback;
    }
    if (caustic_weight_sum > 0.0) {
        caustic_sum = caustic_sum / caustic_weight_sum;
    }

    // Fresnel-lite mix. Full model comes in Sprint 7 with proper GGX.
    let f0 = mix(vec3<f32>(0.04), base_colour, metallic);
    let ndl = max(dot(normal, vec3<f32>(0.4, 0.8, 0.4)), 0.05);
    let diffuse = base_colour * ndl * (1.0 - metallic);
    let specular = f0 * reflected_sum;
    let refr = refracted_sum * exp(-absorption);

    var final_colour = diffuse + specular;
    if (any(absorption > vec3<f32>(0.0))) {
        final_colour = final_colour + refr;
    }
    // Nova3D 0c0c890 caustic-emitter contribution — additive on top of
    // the base lit + refraction result. Emitter energy is already
    // spread by the anisotropic Gaussian, so no further modulation.
    final_colour = final_colour + caustic_sum;
    return vec4<f32>(final_colour, 1.0);
}
