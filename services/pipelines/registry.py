from services.pipelines.steps.step_00_ingest import step_00_ingest
from services.pipelines.steps.step_01_preflight import step_01_preflight
from services.pipelines.steps.step_02_segment import step_02_segment
from services.pipelines.steps.step_03_reconstruct_mesh import step_03_reconstruct_mesh
from services.pipelines.steps.step_04_video_recon_colmap import step_04_video_recon_colmap
from services.pipelines.steps.step_06_pointcloud_to_cad import step_06_pointcloud_to_cad
from services.pipelines.steps.step_07_image_to_cad import step_07_image_to_cad
from services.pipelines.steps.step_08_text_to_cad import step_08_text_to_cad
from services.pipelines.steps.step_09_validate_and_repair import step_09_validate_and_repair
from services.pipelines.steps.step_10_export_step import step_10_export_step
from services.pipelines.steps.step_11_bundle_and_report import step_11_bundle_and_report

STEP_REGISTRY = {
    "step_00_ingest": step_00_ingest,
    "step_01_preflight": step_01_preflight,
    "step_02_segment": step_02_segment,
    "step_03_reconstruct_mesh": step_03_reconstruct_mesh,
    "step_04_video_recon_colmap": step_04_video_recon_colmap,
    "step_06_pointcloud_to_cad": step_06_pointcloud_to_cad,
    "step_07_image_to_cad": step_07_image_to_cad,
    "step_08_text_to_cad": step_08_text_to_cad,
    "step_09_validate_and_repair": step_09_validate_and_repair,
    "step_10_export_step": step_10_export_step,
    "step_11_bundle_and_report": step_11_bundle_and_report,
}
