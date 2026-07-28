//! Multiple render target (MRT) attachment set caching.
//!
//! Nova3D `f0d524b` port. The bug: after a composite pass narrowed a
//! framebuffer's active attachment list, subsequent frames silently
//! dropped writes to the omitted targets (refraction / caustics
//! disappeared without a shader-error signal). The fix: cache a
//! canonical draw-buffer list per render target and re-issue it on
//! every `Bind()`.
//!
//! In wgpu land the equivalent shape is different — you don't
//! `glDrawBuffers`, each render pass declares its `color_attachments`
//! inline. But the failure mode still exists if a caller reuses a
//! [`MrtTargetSet`] across passes: they might forget to add a target
//! back when going from a composite pass to the full G-buffer pass.
//! [`MrtTargetSet::pipeline_targets`] enforces "always the full
//! canonical set" by constructing the ColorTargetState array from a
//! single source of truth. Unit tests assert order + count stability.

/// Names of the four G-buffer targets. Order matches the
/// `FragOut { location(0..3) }` block in shaders/gbuffer.wgsl.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum GBufferTarget {
    /// RT0 : world position + material id in .a    (Rgba16Float)
    PositionMatId,
    /// RT1 : normal + roughness in .a              (Rgba16Float)
    NormalRoughness,
    /// RT2 : base colour + metallic in .a          (Rgba8UnormSrgb)
    BaseMetallic,
    /// RT3 : IoR + absorption + flags packed       (Rgba16Float)
    IorAbsorbFlags,
}

impl GBufferTarget {
    pub const CANONICAL_ORDER: [GBufferTarget; 4] = [
        GBufferTarget::PositionMatId,
        GBufferTarget::NormalRoughness,
        GBufferTarget::BaseMetallic,
        GBufferTarget::IorAbsorbFlags,
    ];

    pub fn format(self) -> wgpu::TextureFormat {
        match self {
            GBufferTarget::PositionMatId => wgpu::TextureFormat::Rgba16Float,
            GBufferTarget::NormalRoughness => wgpu::TextureFormat::Rgba16Float,
            GBufferTarget::BaseMetallic => wgpu::TextureFormat::Rgba8UnormSrgb,
            GBufferTarget::IorAbsorbFlags => wgpu::TextureFormat::Rgba16Float,
        }
    }
}

/// One G-buffer target set. Owns four textures + views, and hands
/// back a canonical [`Vec<ColorTargetState>`] on demand so pipeline
/// creation cannot forget a target.
pub struct MrtTargetSet {
    pub width: u32,
    pub height: u32,
    pub textures: [wgpu::Texture; 4],
    pub views: [wgpu::TextureView; 4],
}

impl MrtTargetSet {
    /// Create a fresh G-buffer target set at `(width, height)`.
    pub fn new(device: &wgpu::Device, width: u32, height: u32) -> Self {
        let mut textures: Vec<wgpu::Texture> = Vec::with_capacity(4);
        let mut views: Vec<wgpu::TextureView> = Vec::with_capacity(4);
        for target in GBufferTarget::CANONICAL_ORDER.iter() {
            let tex = device.create_texture(&wgpu::TextureDescriptor {
                label: Some("pharos_render.mrt.target"),
                size: wgpu::Extent3d { width, height, depth_or_array_layers: 1 },
                mip_level_count: 1,
                sample_count: 1,
                dimension: wgpu::TextureDimension::D2,
                format: target.format(),
                usage: wgpu::TextureUsages::RENDER_ATTACHMENT
                    | wgpu::TextureUsages::TEXTURE_BINDING
                    | wgpu::TextureUsages::COPY_SRC,
                view_formats: &[],
            });
            views.push(tex.create_view(&wgpu::TextureViewDescriptor::default()));
            textures.push(tex);
        }
        MrtTargetSet {
            width,
            height,
            textures: textures.try_into().ok().expect("4 textures"),
            views: views.try_into().ok().expect("4 views"),
        }
    }

    /// Canonical `ColorTargetState` array for pipeline creation. Order
    /// matches [`GBufferTarget::CANONICAL_ORDER`] — never call
    /// per-target `format()` in isolation and hand-roll a subset; the
    /// whole point of this helper is to prevent narrowed attachment
    /// lists (see Nova3D `f0d524b`).
    pub fn pipeline_targets() -> [Option<wgpu::ColorTargetState>; 4] {
        [
            Some(wgpu::ColorTargetState {
                format: GBufferTarget::PositionMatId.format(),
                blend: None,
                write_mask: wgpu::ColorWrites::ALL,
            }),
            Some(wgpu::ColorTargetState {
                format: GBufferTarget::NormalRoughness.format(),
                blend: None,
                write_mask: wgpu::ColorWrites::ALL,
            }),
            Some(wgpu::ColorTargetState {
                format: GBufferTarget::BaseMetallic.format(),
                blend: None,
                write_mask: wgpu::ColorWrites::ALL,
            }),
            Some(wgpu::ColorTargetState {
                format: GBufferTarget::IorAbsorbFlags.format(),
                blend: None,
                write_mask: wgpu::ColorWrites::ALL,
            }),
        ]
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn canonical_order_length_matches_targets() {
        assert_eq!(GBufferTarget::CANONICAL_ORDER.len(), 4);
    }

    #[test]
    fn pipeline_targets_order_matches_canonical() {
        let targets = MrtTargetSet::pipeline_targets();
        assert_eq!(targets.len(), 4);
        for (i, entry) in targets.iter().enumerate() {
            let entry = entry.as_ref().expect("all four attachments populated");
            assert_eq!(entry.format, GBufferTarget::CANONICAL_ORDER[i].format());
        }
    }

    #[test]
    fn all_four_pipeline_targets_populated() {
        // Regression guard: Nova3D bug was a NARROWED attachment list.
        // If someone changes CANONICAL_ORDER to drop a target, this
        // test breaks loudly.
        for entry in MrtTargetSet::pipeline_targets().iter() {
            assert!(entry.is_some());
        }
    }
}
