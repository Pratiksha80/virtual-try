# Initialize all AI engine components
from .model_downloader import ensure_model
from .person_pose import infer_keypoints
from .warp_mesh import warp_rgba_mesh
from .cloth_cleaner import clean_cloth
from .segmentation import ClothSegmentation

__all__ = ['ensure_model', 'infer_keypoints', 'warp_rgba_mesh', 'clean_cloth', 'segmentation']

# Initialize models
MODEL_PATHS = ensure_model()

# Initialize models
segmentation = ClothSegmentation()
