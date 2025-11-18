# backend/routes/tryon.py
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
import os, shutil, base64, uuid, sys, asyncio, time, requests
from PIL import Image
from io import BytesIO
from urllib.parse import urlparse
from typing import Dict, Optional, Tuple

# Add the backend directory to Python path to ensure imports work
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

# Simple in-memory job store (small scale). For production, use Redis or DB.
job_statuses: Dict[str, Dict] = {}


async def validate_and_save_image(image_data: bytes, save_path: str) -> bool:
    """Validate image bytes with PIL and save a normalized PNG to save_path."""
    try:
        img = Image.open(BytesIO(image_data))
        img.verify()

        # Reopen to perform conversions
        img = Image.open(BytesIO(image_data))
        if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
            try:
                # Convert to RGBA first to handle all transparency cases
                img = img.convert("RGBA")
                bg = Image.new("RGBA", img.size, (255, 255, 255, 255))
                bg.paste(img, mask=img.split()[3])
                img = bg.convert("RGB")  # Final conversion to RGB
            except Exception as e:
                print(f"Warning: Transparency conversion failed: {e}")
                img = img.convert("RGB")  # Fallback to direct RGB conversion
        elif img.mode != "RGB":
            img = img.convert("RGB")

        # Resize if too large
        max_size = int(os.getenv("VTRY_MAX_IMG_SIDE", "1024"))
        if max(img.size) > max_size:
            ratio = max_size / max(img.size)
            new_size = tuple(int(dim * ratio) for dim in img.size)
            img = img.resize(new_size, Image.LANCZOS)

        # Ensure folder exists
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        img.save(save_path, "PNG", optimize=True)
        return True
    except Exception as e:
        print(f"Image validation failed: {e}")
        return False


async def fetch_image_bytes(url: str, timeout: int = 30) -> Optional[bytes]:
    """Download image bytes from a URL using requests in a thread; if HTML is returned, try several strategies to locate the product image.
    This function is robust to Amazon/Flipkart product pages by checking og:image, data-a-dynamic-image, JSON-LD, and link rel=image_src.
    """
    def sync_fetch(u: str, to: int):
        headers_list = [
            {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36'},
            {'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15A372 Safari/604.1'},
        ]

        # Try a few attempts with different headers
        for attempt in range(3):
            for headers in headers_list:
                try:
                    r = requests.get(u, timeout=to, headers=headers, allow_redirects=True)
                    status = r.status_code
                    content_type = r.headers.get('content-type', '')
                    data = r.content
                    print(f"fetch attempt {attempt+1} headers={headers['User-Agent'][:40]} status={status} ctype={content_type} url={r.url}")

                    # If direct image, return bytes
                    if content_type and content_type.split(';')[0].startswith('image/'):
                        return data

                    # If HTML or unknown, attempt to extract candidate image URLs
                    text = data.decode('utf-8', errors='ignore')

                    # 1) meta og:image
                    import re
                    m = re.search(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']', text, re.I)
                    if not m:
                        m = re.search(r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\']', text, re.I)
                    if m:
                        img_url = m.group(1)
                        img_url = img_url.strip()
                        if img_url.startswith('//'):
                            img_url = 'https:' + img_url
                        elif img_url.startswith('/'):
                            parsed = urlparse(r.url)
                            img_url = f"{parsed.scheme}://{parsed.netloc}{img_url}"
                        try:
                            r2 = requests.get(img_url, timeout=to, headers=headers)
                            if r2.headers.get('content-type', '').split(';')[0].startswith('image/'):
                                print(f"Found og:image -> {img_url}")
                                return r2.content
                        except Exception as e:
                            print(f"og:image fetch failed: {e}")

                    # 2) Amazon specific: data-a-dynamic-image attribute contains JSON mapping
                    m2 = re.search(r'data-a-dynamic-image=\"(\\{.*?\\})\"', text, re.DOTALL)
                    if m2:
                        try:
                            import json
                            json_str = m2.group(1).replace('\\\"', '"').replace('&quot;', '"')
                            mapping = json.loads(json_str)
                            # Sort by image size (largest first)
                            urls = sorted(mapping.keys(), key=lambda x: mapping[x][0] * mapping[x][1] if isinstance(mapping[x], list) else 0, reverse=True)
                            for k in urls:
                                try:
                                    r3 = requests.get(k, timeout=to, headers=headers)
                                    if r3.headers.get('content-type', '').split(';')[0].startswith('image/'):
                                        print(f"Found data-a-dynamic-image -> {k}")
                                        return r3.content
                                except Exception as e:
                                    print(f"Failed to fetch image {k}: {e}")
                                    continue
                        except Exception as e:
                            print(f"data-a-dynamic-image parse failed: {e}")

                    # 3) JSON-LD: look for "image": "..."
                    m3 = re.search(r'"image"\s*:\s*"([^"]+)"', text)
                    if m3:
                        img_url = m3.group(1)
                        try:
                            r4 = requests.get(img_url, timeout=to, headers=headers)
                            if r4.headers.get('content-type', '').split(';')[0].startswith('image/'):
                                print(f"Found JSON-LD image -> {img_url}")
                                return r4.content
                        except Exception:
                            pass

                    # 4) link rel=image_src
                    m4 = re.search(r'<link[^>]+rel=["\']image_src["\'][^>]+href=["\']([^"\']+)["\']', text, re.I)
                    if m4:
                        img_url = m4.group(1)
                        try:
                            r5 = requests.get(img_url, timeout=to, headers=headers)
                            if r5.headers.get('content-type', '').split(';')[0].startswith('image/'):
                                print(f"Found image_src -> {img_url}")
                                return r5.content
                        except Exception:
                            pass

                    # 5) <img> tags: src, data-src, data-old-hires, srcset
                    # Prefer the largest candidate found in srcset or the explicit attributes
                    try:
                        imgs = re.findall(r'<img[^>]+>', text, re.I)
                        candidates = []
                        for img_tag in imgs:
                            # extract src/srcset/data-src/data-old-hires
                            src_match = re.search(r'src=["\']([^"\']+)["\']', img_tag, re.I)
                            data_src = re.search(r'data-src=["\']([^"\']+)["\']', img_tag, re.I)
                            old_hires = re.search(r'data-old-hires=["\']([^"\']+)["\']', img_tag, re.I)
                            srcset = re.search(r'srcset=["\']([^"\']+)["\']', img_tag, re.I)

                            if srcset:
                                # parse srcset and pick the largest width candidate
                                parts = [p.strip() for p in srcset.group(1).split(',') if p.strip()]
                                for part in parts:
                                    sub = part.split()
                                    url_candidate = sub[0]
                                    # try to pick the one with width descriptor if present
                                    width = None
                                    if len(sub) > 1 and sub[1].endswith('w'):
                                        try:
                                            width = int(sub[1][:-1])
                                        except Exception:
                                            width = None
                                    candidates.append((width or 0, url_candidate))
                            if old_hires:
                                candidates.append((0, old_hires.group(1)))
                            if data_src:
                                candidates.append((0, data_src.group(1)))
                            if src_match:
                                candidates.append((0, src_match.group(1)))

                        # sort by width desc to prefer larger images
                        if candidates:
                            candidates_sorted = sorted(candidates, key=lambda x: x[0], reverse=True)
                            for _, cand in candidates_sorted:
                                cand_url = cand.strip()
                                if not cand_url:
                                    continue
                                if cand_url.startswith('//'):
                                    cand_url = 'https:' + cand_url
                                elif cand_url.startswith('/'):
                                    parsed = urlparse(r.url)
                                    cand_url = f"{parsed.scheme}://{parsed.netloc}{cand_url}"
                                try:
                                    r_img = requests.get(cand_url, timeout=to, headers=headers)
                                    if r_img.headers.get('content-type', '').split(';')[0].startswith('image/') and len(r_img.content) > 2000:
                                        print(f"Found image via <img> tag -> {cand_url}")
                                        return r_img.content
                                except Exception:
                                    continue
                    except Exception as e:
                        print(f"img tag parsing failed: {e}")

                    # If we reach here, we didn't find an image this round; try next headers/attempt
                    time.sleep(0.5)
                except Exception as e:
                    print(f"sync_fetch inner error: {e}")
                    continue

        return None

    return await asyncio.to_thread(sync_fetch, url, timeout)


async def capture_cloth_image(link: str, save_path: str) -> Tuple[bool, str]:
    """Try to obtain a cloth image for the product link and save it to save_path.
    Returns (success: bool, message: str).
    """
    try:
        data = await fetch_image_bytes(link, timeout=30)
        if not data:
            msg = "No data fetched from the provided link"
            print(msg)
            return False, msg

        # Validate and save
        ok = await validate_and_save_image(data, save_path)
        if ok:
            return True, "OK"

        # If validate failed, possibly data was HTML; try to extract og:image and download again
        text = data.decode("utf-8", errors="ignore")
        import re
        m = re.search(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']', text, re.I)
        if not m:
            m = re.search(r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\']', text, re.I)
        if m:
            img_url = m.group(1)
            if img_url.startswith("//"):
                img_url = "https:" + img_url
            elif img_url.startswith("/"):
                parsed = urlparse(link)
                img_url = f"{parsed.scheme}://{parsed.netloc}{img_url}"
            data2 = await fetch_image_bytes(img_url, timeout=30)
            if data2:
                ok2 = await validate_and_save_image(data2, save_path)
                if ok2:
                    return True, "OK (og:image)"
                else:
                    return False, "Downloaded og:image but validation failed"

        # As a last resort, attempt to use a headless browser to render the page and extract images
        try:
            ok, pm = await playwright_fetch_image(link, save_path)
            if ok:
                return True, pm
            else:
                return False, f"Unable to locate a valid product image from the link (playwright: {pm})"
        except NameError:
            # playwright_fetch_image not defined (older code path)
            return False, "Unable to locate a valid product image from the link"
    except Exception as e:
        msg = f"capture_cloth_image failed: {e}"
        print(msg)
        return False, msg


async def playwright_fetch_image(url: str, save_path: str, timeout: int = 30000) -> Tuple[bool, str]:
    """Use Playwright to render the page and extract the product image. Returns (ok, message)."""
    try:
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            return False, "Playwright not installed. Install with: pip install playwright && python -m playwright install"

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            try:
                await page.goto(url, timeout=timeout)
            except Exception as e:
                await browser.close()
                return False, f"Playwright failed to load page: {e}"

            # Try common selectors used by Amazon/Flipkart and general product pages
            selectors = [
                '#landingImage', 'img#landingImage', 'img.a-dynamic-image',
                'img[data-old-hires]', '.image-gallery img', 'img[data-src]'
            ]
            src = None
            for sel in selectors:
                try:
                    el = await page.query_selector(sel)
                    if el:
                        src = await el.get_attribute('src') or await el.get_attribute('data-old-hires') or await el.get_attribute('data-src')
                        if src:
                            src = src.strip()
                            break
                except Exception:
                    continue

            # Try og:image meta
            if not src:
                try:
                    og = await page.get_attribute('meta[property="og:image"]', 'content')
                    if og:
                        src = og.strip()
                except Exception:
                    src = None

            await browser.close()

            if not src:
                return False, 'Playwright could not find image src on page'

            # Normalize src
            if src.startswith('//'):
                src = 'https:' + src
            elif src.startswith('/'):
                parsed = urlparse(url)
                src = f"{parsed.scheme}://{parsed.netloc}{src}"

            # Download the image bytes (requests in thread)
            def sync_download(u: str, to: int):
                try:
                    r = requests.get(u, timeout=to, headers={'User-Agent': 'Mozilla/5.0'})
                    if r.status_code == 200 and r.headers.get('content-type', '').split(';')[0].startswith('image/'):
                        return r.content
                    return None
                except Exception as e:
                    print(f"playwright sync_download failed: {e}")
                    return None

            data = await asyncio.to_thread(sync_download, src, 30)
            if not data:
                return False, f"Failed to download image from extracted src: {src}"

            ok = await validate_and_save_image(data, save_path)
            if ok:
                return True, 'OK (playwright)'
            else:
                return False, 'Downloaded image from page but validation failed'
    except Exception as e:
        return False, f'Playwright fetch error: {e}'


async def process_tryon_job(job_id: str, user_img_path: str, cloth_img_path: str, cloth_type: str, timeout_seconds: int = 300):
    """Background worker that runs the tryon process and stores result in job_statuses."""
    import traceback

    # Initialize job status and logs
    job_statuses[job_id] = {"status": "queued", "created_at": time.time(), "logs": []}
    def log(msg: str):
        print(f"[job {job_id}] {msg}")
        job_statuses[job_id].setdefault("logs", []).append(f"{time.time()}: {msg}")

    try:
        job_statuses[job_id]["status"] = "processing"
        log("Started processing")

        # Validate that tryon_process is available
        if not tryon_process:
            err = "tryon_process function not available"
            log(err)
            job_statuses[job_id].update({"status": "failed", "error": err, "completed_at": time.time()})
            return

        # Check input files exist and report sizes
        for path_label, p in (("user_img", user_img_path), ("cloth_img", cloth_img_path)):
            try:
                if not p or not os.path.exists(p):
                    log(f"Missing file for {path_label}: {p}")
                    job_statuses[job_id].update({"status": "failed", "error": f"Missing file: {p}", "completed_at": time.time()})
                    return
                size = os.path.getsize(p)
                log(f"{path_label} exists: {p} ({size} bytes)")
            except Exception as e:
                log(f"Error checking file {p}: {e}")
                job_statuses[job_id].update({"status": "failed", "error": str(e), "completed_at": time.time()})
                return

        # Run the CPU-bound tryon_process in an executor with timeout
        loop = asyncio.get_event_loop()
        try:
            result = await asyncio.wait_for(
                loop.run_in_executor(None, lambda: tryon_process(user_img_path, cloth_img_path, cloth_type)),
                timeout=timeout_seconds,
            )
        except asyncio.TimeoutError:
            err = "Processing timed out"
            log(err)
            job_statuses[job_id].update({"status": "failed", "error": err, "completed_at": time.time()})
            return
        except Exception as e:
            tb = traceback.format_exc()
            log(f"Exception while running tryon_process: {e}\n{tb}")
            job_statuses[job_id].update({"status": "failed", "error": str(e), "traceback": tb, "completed_at": time.time()})
            return

        # Validate result structure
        if not result or not isinstance(result, dict):
            err = "Invalid result from tryon_process"
            log(err)
            job_statuses[job_id].update({"status": "failed", "error": err, "result_raw": repr(result), "completed_at": time.time()})
            return

        if "output_image_base64" not in result:
            err = "Missing output_image_base64 in tryon result"
            log(err)
            job_statuses[job_id].update({"status": "failed", "error": err, "result_keys": list(result.keys()), "completed_at": time.time()})
            return

        # Store success result
        job_statuses[job_id].update({"status": "completed", "result": result, "completed_at": time.time()})
        log("Processing completed successfully")

    except Exception as e:
        tb = traceback.format_exc()
        log(f"Unexpected error: {e}\n{tb}")
        job_statuses[job_id].update({"status": "failed", "error": str(e), "traceback": tb, "completed_at": time.time()})
    finally:
        # Clean up input files to save disk space
        for p in (user_img_path, cloth_img_path):
            try:
                if p and os.path.exists(p):
                    os.remove(p)
                    log(f"Removed file {p}")
            except Exception as e:
                log(f"Failed to remove file {p}: {e}")

# Import AI modules
try:
    from ai_engine.tryon_processor import process_tryon
    tryon_process = process_tryon
    print("✅ Successfully imported AI engine from tryon_processor")
except ImportError as e:
    print(f"⚠️ AI modules import failed: {e}")
    tryon_process = None
    print("⚠️ AI engine temporarily disabled due to import issues")

router = APIRouter()


@router.get("/debug/job/last")
async def debug_get_last_job():
    """Return the most recently created job_id for quick inspection (or 404)."""
    if not job_statuses:
        raise HTTPException(status_code=404, detail="No jobs found")
    # job_statuses keys are unordered; pick the most recently created by timestamp
    latest = None
    latest_ts = 0
    for jid, info in job_statuses.items():
        ts = info.get("created_at", 0)
        if ts and ts > latest_ts:
            latest_ts = ts
            latest = jid
    if not latest:
        # fallback: pick any
        latest = next(iter(job_statuses.keys()))
    return {"job_id": latest, "status": job_statuses[latest].get("status")}


@router.get("/debug/job/{job_id}/logs")
async def debug_get_job_logs(job_id: str):
    """Return logs, error, and traceback for a job to help debugging."""
    if job_id not in job_statuses:
        raise HTTPException(status_code=404, detail="Job not found")
    info = job_statuses[job_id]
    return {
        "job_id": job_id,
        "status": info.get("status"),
        "logs": info.get("logs", []),
        "error": info.get("error"),
        "traceback": info.get("traceback"),
        "result_keys": list(info.get("result", {}).keys()) if info.get("result") else None,
    }

@router.get("/job/{job_id}")
async def get_job_status(job_id: str):
    """Get the status of a try-on job"""
    if job_id not in job_statuses:
        raise HTTPException(status_code=404, detail="Job not found")
    return job_statuses[job_id]

@router.post("/tryon")
async def tryon_simple(
    user_image: str,
    cloth_image: str,
    cloth_type: str = "shirt"
):
    """Simple try-on endpoint for testing."""
    print(f"\n🔵 Processing simple try-on request:")
    print(f"User image: {user_image}")
    print(f"Cloth image: {cloth_image}")
    print(f"Cloth type: {cloth_type}\n")
    
    try:
        if not tryon_process:
            raise HTTPException(status_code=500, detail="tryon_process function not available")

        result = tryon_process(user_image, cloth_image, cloth_type)
        
        # normalize and validate result from processor
        if not result or not isinstance(result, dict):
            raise HTTPException(status_code=500, detail="Invalid result format from tryon_process")

        if "error" in result and result.get("output_image_base64") in (None, ""):
            # If processor returned an error and no image, report it
            raise HTTPException(status_code=500, detail=result.get("error") or "Unknown processing error")

        # Backwards-compatibility: accept either a direct 'output_image_base64' key
        # or a nested 'result' dict that contains the image.
        if "output_image_base64" in result and result.get("output_image_base64"):
            return result

        if "result" in result and isinstance(result["result"], dict) and result["result"].get("output_image_base64"):
            # Return nested result for compatibility with older frontends
            return result["result"]

        # If we reach here, the processor did not provide an output image
        raise HTTPException(status_code=500, detail="Try-on completed but no output image was produced")
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"⚠️ Error in simple try-on: {str(e)}")
        print("Stack trace:", e.__traceback__)
        raise HTTPException(status_code=500, detail=f"Try-on failed: {str(e)}")

@router.post("/tryon/link")
async def tryon_link(
    background_tasks: BackgroundTasks,
    link: str = Form(...),
    cloth_type: str = Form(...),
    image: UploadFile = File(...)
):
    # Increase timeout for the route
    timeout_seconds = 120  # 2 minutes timeout
    print(f"\n🔵 Processing try-on request:")
    print(f"Link: {link}")
    print(f"Cloth type: {cloth_type}")
    
    user_img_path = None
    cloth_img_path = None
    
    try:
        # Create directories
        for dir_path in ['uploads/user', 'uploads/cloth', 'uploads/debug']:
            os.makedirs(dir_path, exist_ok=True)
            
        # Handle user image with optimization
        contents = await image.read()
        if len(contents) > 2 * 1024 * 1024:  # 2MB limit
            raise HTTPException(status_code=413, detail="Image too large. Maximum size is 2MB")
        
        # Optimize image before processing
        try:
            img = Image.open(BytesIO(contents))
            # Convert to RGB and resize if needed
            if img.mode != 'RGB':
                img = img.convert('RGB')
            # Resize to maximum dimension of 800px
            max_size = 800
            if max(img.size) > max_size:
                ratio = max_size / max(img.size)
                new_size = tuple(int(dim * ratio) for dim in img.size)
                img = img.resize(new_size, Image.LANCZOS)
            # Save optimized image to BytesIO
            optimized = BytesIO()
            img.save(optimized, format='JPEG', quality=85, optimize=True)
            contents = optimized.getvalue()
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Image optimization failed: {str(e)}")
            
        user_img_path = f"uploads/user/user_{uuid.uuid4()}.png"
        if not await validate_and_save_image(contents, user_img_path):
            raise HTTPException(status_code=400, detail="Invalid user image format")
            
        # Handle cloth image
        cloth_img_path = f"uploads/cloth/cloth_{uuid.uuid4()}.png"

        ok, msg = await capture_cloth_image(link, cloth_img_path)
        if not ok:
            raise HTTPException(status_code=400, detail=f"Failed to capture product image: {msg}")

        if not tryon_process:
            raise HTTPException(status_code=500, detail="Try-on processor not available")

        # Enqueue background job and return job_id immediately
        job_id = uuid.uuid4().hex
        job_statuses[job_id] = {"status": "created", "created_at": time.time()}

        # Start background processing task
        asyncio.create_task(process_tryon_job(job_id, user_img_path, cloth_img_path, cloth_type, timeout_seconds))

        return {"status": "accepted", "job_id": job_id}
            
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Try-on failed: {str(e)}")
    finally:
        # NOTE: Do NOT remove the saved user/clothing files here — background
        # worker (process_tryon_job) is responsible for cleaning them after
        # processing completes. Removing them here causes the background job
        # to fail with "file not found" or processing errors.
        # If the uploaded `image` is a SpooledTemporaryFile or similar, ensure
        # it's closed (handled by starlette), but leave saved paths intact.
        pass
    
