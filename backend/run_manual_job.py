import asyncio, importlib, time

# Import the module
m = importlib.import_module('backend.routes.tryon')
# pick sample files (existing in repo)
user = r'd:/Virtual-Try/backend/uploads/user/user_5d753be0-c88d-4b8c-842c-b83629034a1d.png'
cloth = r'd:/Virtual-Try/backend/uploads/cloth/cloth_008a771b9e2b43198aa18b3f1acad278.png'
job_id = 'manualtest_' + str(int(time.time()))
print('Starting job', job_id)

# run the background worker directly (sync)
asyncio.run(m.process_tryon_job(job_id, user, cloth, 'shirt', timeout_seconds=120))

print('Job finished. Status:')
import json
print(json.dumps(m.job_statuses.get(job_id, {}), indent=2))
