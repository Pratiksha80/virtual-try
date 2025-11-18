# VITON-HD Model Files

This directory needs the following model files for the virtual try-on system to work:

Required files:
1. `clothformer_base.pth` - ClothFormer base model
2. `parser.pth` - Image parsing model
3. `pose_estimator.pth` - Human pose estimation model

## Manual Setup Instructions

1. Obtain the model files from one of these sources:
   - Project maintainer
   - Official project repository
   - Trained models backup

2. Place the files directly in this directory (`backend/ai_engine/models/`)

3. Verify file placement:
   ```
   backend/ai_engine/models/
   ├── clothformer_base.pth
   ├── parser.pth
   └── pose_estimator.pth
   ```

4. Restart the backend server after placing the files

## Troubleshooting

If you see "Processing Failed" errors, check:
1. All three model files are present in this directory
2. File names match exactly as listed above
3. Files are complete and not corrupted