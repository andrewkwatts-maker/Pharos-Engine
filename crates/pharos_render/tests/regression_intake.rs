//! Sprint 1 regression suite — locks in the Nova3D bug ports so a
//! lazy refactor can't silently regress them. Each test names the
//! Nova3D SHA + one-line failure mode so the git-blame reader knows
//! exactly what breaks.

use pharos_render::backend::{GBufferTarget, MrtTargetSet};

/// Nova3D `f0d524b` — the MRT draw-buffer list must always contain
/// the full canonical G-buffer set. If someone trims one of the four
/// attachments, refraction / caustics silently break in composite
/// passes.
#[test]
fn f0d524b_mrt_canonical_set_has_four_targets() {
    let targets = MrtTargetSet::pipeline_targets();
    assert_eq!(targets.len(), 4);
    for entry in targets.iter() {
        assert!(entry.is_some(), "each of the four G-buffer targets must be populated");
    }
}

#[test]
fn f0d524b_canonical_order_stable() {
    // gbuffer.wgsl's FragOut writes locations 0..3 in this exact
    // order. If Rust and WGSL disagree, the wrong texture takes the
    // wrong data.
    assert_eq!(GBufferTarget::CANONICAL_ORDER[0], GBufferTarget::PositionMatId);
    assert_eq!(GBufferTarget::CANONICAL_ORDER[1], GBufferTarget::NormalRoughness);
    assert_eq!(GBufferTarget::CANONICAL_ORDER[2], GBufferTarget::BaseMetallic);
    assert_eq!(GBufferTarget::CANONICAL_ORDER[3], GBufferTarget::IorAbsorbFlags);
}

/// Nova3D `96a23e0` — vcr_seed.wgsl's refract() branch must guard
/// against TIR (total internal reflection) producing a degenerate
/// vec3(0.0) direction that would poison env-cube sampling downstream.
#[test]
fn f96a23e0_vcr_seed_has_tir_refract_guard() {
    let src = include_str!("../shaders/vcr_seed.wgsl");
    assert!(
        src.contains("Nova3D 96a23e0"),
        "vcr_seed.wgsl must carry the 96a23e0 guard comment",
    );
    assert!(
        src.contains("dot(refr, refr) < 1e-4"),
        "vcr_seed.wgsl must guard against TIR-produced degenerate refract() output",
    );
    assert!(
        src.contains("refr = refl"),
        "vcr_seed.wgsl TIR fallback must reuse the reflection direction",
    );
}

/// Nova3D `4fe12cb` — vcr_composite.wgsl falls back to lit-colour
/// when no reservoir slot contributes a reflection sample (avoids
/// the dark-rim halo on transparent silhouettes when SSR is off).
#[test]
fn f4fe12cb_composite_has_lit_colour_fallback() {
    let src = include_str!("../shaders/vcr_composite.wgsl");
    assert!(src.contains("Nova3D") && src.contains("halo"));
    assert!(src.contains("lit_colour"));
    assert!(src.contains("textureSampleLevel(lit_colour"));
}

/// Nova3D `3d21abd` — the RefractComposite black-sample fallback is
/// covered by the same ssr_fallback / total_weight branch.
#[test]
fn f3d21abd_composite_covers_refract_black_sample() {
    let src = include_str!("../shaders/vcr_composite.wgsl");
    assert!(src.contains("ssr_fallback"));
    assert!(src.contains("total_weight"));
}

/// Nova3D `39cc44a` — the HiZ pyramid build must seed mip 0 from the
/// current-frame depth attachment before the downsample chain runs.
/// Missing this write leaves mip 0 undefined on cold init / resize,
/// which silently corrupts SSR + VCR frustum culling.
#[test]
fn f39cc44a_hiz_shader_seeds_mip_zero() {
    let src = include_str!("../shaders/hiz_seed.wgsl");
    assert!(
        src.contains("Nova3D 39cc44a"),
        "hiz_seed.wgsl must carry the 39cc44a guard comment",
    );
    assert!(
        src.contains("fn hiz_seed"),
        "hiz_seed.wgsl must expose the hiz_seed compute entry point",
    );
    assert!(
        src.contains("textureStore(hiz_mip0"),
        "hiz_seed.wgsl must write the depth sample into hiz_mip0",
    );
    assert!(
        src.contains("textureLoad(depth_src"),
        "hiz_seed.wgsl must read from the depth attachment source",
    );
}

/// Nova3D `39cc44a` — the workgroup constant in the Rust module must
/// stay in sync with the `@workgroup_size(8, 8, 1)` annotation in the
/// WGSL shader. If they drift, the dispatch-group math undercounts and
/// the seed pass silently skips the tail rows/columns of mip 0.
#[test]
fn f39cc44a_hiz_workgroup_constant_matches_shader() {
    use pharos_render::pipeline::{HIZ_SEED_WORKGROUP, HiZPipeline};
    assert_eq!(HIZ_SEED_WORKGROUP, (8, 8));
    // Full-coverage dispatch: 100x100 target must round UP to 13x13
    // groups so the last 4-pixel strip is not skipped.
    assert_eq!(HiZPipeline::dispatch_groups(100, 100), (13, 13, 1));

    let src = include_str!("../shaders/hiz_seed.wgsl");
    assert!(
        src.contains("@workgroup_size(8, 8, 1)"),
        "hiz_seed.wgsl workgroup size must match HIZ_SEED_WORKGROUP",
    );
}
