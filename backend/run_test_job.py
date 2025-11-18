import asyncio
import os
import time

# Ensure imports from package
from routes import tryon as tryon_mod

async def main():
    # pick sample files
    user_dir = os.path.join(os.path.dirname(__file__), 'uploads', 'user')
    cloth_dir = os.path.join(os.path.dirname(__file__), 'uploads', 'cloth')
    user_files = [f for f in os.listdir(user_dir) if os.path.isfile(os.path.join(user_dir, f))]
    cloth_files = [f for f in os.listdir(cloth_dir) if os.path.isfile(os.path.join(cloth_dir, f))]
    if not user_files or not cloth_files:
        print('No sample files found in uploads/user or uploads/cloth')
        return
    user_path = os.path.join(user_dir, user_files[0])
    cloth_path = os.path.join(cloth_dir, cloth_files[0])
    print('Using user:', user_path)
    print('Using cloth:', cloth_path)

    job_id = 'testjob_' + str(int(time.time()))
    tryon_mod.job_statuses[job_id] = {'status': 'created', 'created_at': time.time()}
    await tryon_mod.process_tryon_job(job_id, user_path, cloth_path, 'shirt', timeout_seconds=120)

    # print job status
    print('Job status:')
    import json
    print(json.dumps(tryon_mod.job_statuses.get(job_id, {}), indent=2))

if __name__ == '__main__':
    asyncio.run(main())
