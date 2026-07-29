//! Hierarchical-Z (HiZ) depth pyramid — mip-0 seed + downsample chain.
//!
//! Nova3D `39cc44a` port. The historical bug: the pyramid downsample
//! compute pass consumed mip N-1 to produce mip N, but nothing wrote
//! mip 0 from the current-frame depth attachment. On the first frame
//! (and every resize / device-lost recovery) the pyramid was garbage,
//! silently breaking SSR reservoir occlusion tests and VCR frustum
//! culling with no shader-error signal.
//!
//! [`HiZPipeline::seed_mip0`] runs [`shaders/hiz_seed.wgsl`] over the
//! HiZ mip-0 storage texture, sampling the depth attachment. It MUST
//! be dispatched every frame, before the downsample chain — a stale
//! mip 0 from the previous frame corrupts culling once the camera
//! moves.
//!
//! The full downsample chain (mips 1..N via max-pool) is out of scope
//! for this port; this module wires the seed pass alone. When the
//! downsample chain lands it will read the seeded mip 0 and produce
//! the tail of the pyramid in one further dispatch chain.

/// HiZ storage-texture format. Single-channel f32 so mip-0 seed can
/// write the raw depth value and later downsample passes can max-pool
/// with no format conversion.
pub const HIZ_STORAGE_FORMAT: wgpu::TextureFormat = wgpu::TextureFormat::R32Float;

/// Compute workgroup size in the seed shader. Kept as a constant so
/// callers computing dispatch group counts stay in sync with the
/// `@workgroup_size(8, 8, 1)` annotation in `hiz_seed.wgsl`.
pub const HIZ_SEED_WORKGROUP: (u32, u32) = (8, 8);

/// Owns the mip-0 seed compute pipeline + its bind-group layout.
///
/// The layout is intentionally minimal — one depth sample source and
/// one r32float storage output — so it composes with any HiZ texture
/// allocation strategy the caller picks (single-mip storage texture,
/// or a multi-mip texture with only mip 0 bound here).
pub struct HiZPipeline {
    pub seed_pipeline: wgpu::ComputePipeline,
    pub seed_bind_group_layout: wgpu::BindGroupLayout,
}

impl HiZPipeline {
    /// Create the HiZ mip-0 seed compute pipeline.
    pub fn new(device: &wgpu::Device) -> Self {
        let shader = device.create_shader_module(wgpu::ShaderModuleDescriptor {
            label: Some("pharos_render.hiz.seed.shader"),
            source: wgpu::ShaderSource::Wgsl(std::borrow::Cow::Borrowed(include_str!(
                "../../shaders/hiz_seed.wgsl"
            ))),
        });

        let seed_bind_group_layout =
            device.create_bind_group_layout(&wgpu::BindGroupLayoutDescriptor {
                label: Some("pharos_render.hiz.seed.bgl"),
                entries: &[
                    // depth_src: non-multisampled depth texture.
                    wgpu::BindGroupLayoutEntry {
                        binding: 0,
                        visibility: wgpu::ShaderStages::COMPUTE,
                        ty: wgpu::BindingType::Texture {
                            sample_type: wgpu::TextureSampleType::Depth,
                            view_dimension: wgpu::TextureViewDimension::D2,
                            multisampled: false,
                        },
                        count: None,
                    },
                    // hiz_mip0: r32float storage, write-only.
                    wgpu::BindGroupLayoutEntry {
                        binding: 1,
                        visibility: wgpu::ShaderStages::COMPUTE,
                        ty: wgpu::BindingType::StorageTexture {
                            access: wgpu::StorageTextureAccess::WriteOnly,
                            format: HIZ_STORAGE_FORMAT,
                            view_dimension: wgpu::TextureViewDimension::D2,
                        },
                        count: None,
                    },
                ],
            });

        let layout = device.create_pipeline_layout(&wgpu::PipelineLayoutDescriptor {
            label: Some("pharos_render.hiz.seed.layout"),
            bind_group_layouts: &[&seed_bind_group_layout],
            push_constant_ranges: &[],
        });

        let seed_pipeline = device.create_compute_pipeline(&wgpu::ComputePipelineDescriptor {
            label: Some("pharos_render.hiz.seed.pipeline"),
            layout: Some(&layout),
            module: &shader,
            entry_point: "hiz_seed",
            compilation_options: Default::default(),
        });

        Self {
            seed_pipeline,
            seed_bind_group_layout,
        }
    }

    /// Compute the workgroup-count triple for a dispatch that covers
    /// every pixel of a `width x height` HiZ mip-0 texture. The shader
    /// early-outs on out-of-bounds threads so callers may round up
    /// safely — this helper does exactly that.
    pub fn dispatch_groups(width: u32, height: u32) -> (u32, u32, u32) {
        let (gx, gy) = HIZ_SEED_WORKGROUP;
        (width.div_ceil(gx), height.div_ceil(gy), 1)
    }

    /// Encode the mip-0 seed dispatch into the given compute pass.
    /// Callers must have already set the bind group containing the
    /// depth source view + the mip-0 storage view; this helper only
    /// binds the pipeline and issues the dispatch. The
    /// `dispatch_groups` helper computes the correct group counts.
    pub fn encode_seed<'a>(
        &'a self,
        pass: &mut wgpu::ComputePass<'a>,
        groups: (u32, u32, u32),
    ) {
        pass.set_pipeline(&self.seed_pipeline);
        pass.dispatch_workgroups(groups.0, groups.1, groups.2);
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn dispatch_groups_rounds_up() {
        // A 100x100 target with workgroup 8x8 needs 13x13 groups
        // (12x12 = 96x96 would miss the last 4-pixel row and column).
        assert_eq!(HiZPipeline::dispatch_groups(100, 100), (13, 13, 1));
    }

    #[test]
    fn dispatch_groups_exact_multiple() {
        assert_eq!(HiZPipeline::dispatch_groups(64, 32), (8, 4, 1));
    }

    #[test]
    fn dispatch_groups_zero_target_is_zero_groups() {
        assert_eq!(HiZPipeline::dispatch_groups(0, 0), (0, 0, 1));
    }
}
