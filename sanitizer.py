import io
import os
import json
import uuid
import urllib.parse
from fastapi import FastAPI, File, UploadFile, HTTPException, Response, Request, Form
from fastapi.responses import RedirectResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from PIL import Image, ExifTags, UnidentifiedImageError, ImageOps
import pillow_heif
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

#prevent decompression bombs
Image.MAX_IMAGE_PIXELS = 50_000_000

pillow_heif.register_heif_opener()
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(title="Image Sanitization Service", version="1.1.0")
app.mount("/static", StaticFiles(directory="static"), name="static")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.get("/", include_in_schema=False)
async def root():
    html_path = os.path.join(os.path.dirname(__file__), "index.html")
    if os.path.exists(html_path):
        return FileResponse(html_path)
    return RedirectResponse(url="/docs")

@app.post("/sanitize/")
@limiter.limit("5/minute")
async def sanitize_image(
    request: Request, 
    file: UploadFile = File(...),
    strip_gps: bool = Form(True),
    strip_device: bool = Form(True),
    keep_copyright: bool = Form(False),
    output_format: str = Form("original"),
    scramble_filename: bool = Form(False)
):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Invalid file type.")

    MAX_FILE_SIZE = 10 * 1024 * 1024
    if file.size and file.size > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large.")

    try:
        image_data = await file.read()
        if len(image_data) > MAX_FILE_SIZE:
            raise HTTPException(status_code=413, detail="File too large.")

        image = Image.open(io.BytesIO(image_data))
        image = ImageOps.exif_transpose(image)
        stripped_metadata = {}

        def clean_value(val):
            if isinstance(val, bytes):
                val = val.decode('utf-8', errors='ignore')
            val_str = str(val)
            if len(val_str) > 100:
                return val_str[:100] + "... [TRUNCATED]"
            return val_str

        exif_data = image.getexif()
        if exif_data:
            tags_to_keep = {274, 40961, 40962, 40963} 
            
            if not strip_device:
                tags_to_keep.update([271, 272, 305, 42035, 42036])
            if keep_copyright:
                tags_to_keep.update([315, 33432])
            if not strip_gps:
                tags_to_keep.add(34853)

            for ifd_id in ExifTags.IFD:
                try:
                    if ifd_id not in tags_to_keep and ifd_id in exif_data:
                        ifd_data = exif_data.get_ifd(ifd_id)
                        for sub_id, sub_val in ifd_data.items():
                            tag_name = ExifTags.GPSTAGS.get(sub_id, sub_id) if ifd_id == ExifTags.IFD.GPSInfo else ExifTags.TAGS.get(sub_id, sub_id)
                            stripped_metadata[f"{ifd_id.name}:{tag_name}"] = clean_value(sub_val)
                        del exif_data[ifd_id]
                except KeyError:
                    pass

            for tag_id in list(exif_data.keys()):
                if tag_id not in tags_to_keep and tag_id not in ExifTags.IFD:
                    val = exif_data[tag_id]
                    tag_name = ExifTags.TAGS.get(tag_id, tag_id)
                    stripped_metadata[f"EXIF:{tag_name}"] = clean_value(val)
                    del exif_data[tag_id]
            
            exif_bytes = exif_data.tobytes()
        else:
            exif_bytes = b""

        if image.info:
            for key, value in image.info.items():
                if key not in ("exif", "icc_profile"): 
                    stripped_metadata[f"Info:{key}"] = clean_value(value)

        image.info.clear()
        clean_io = io.BytesIO()
        
        #handle format conversions
        save_format = image.format if image.format else "JPEG"
        if output_format.lower() != "original" and output_format.lower() in ("jpeg", "png", "webp"):
            save_format = output_format.upper()
        
        if save_format.upper() in ("HEIF", "HEIC"):
            save_format = "JPEG"

        if save_format.upper() in ("JPEG", "BMP") and image.mode in ("RGBA", "P"):
            image = image.convert("RGB")
            
        image.save(clean_io, format=save_format, icc_profile=b"", exif=exif_bytes)
        clean_bytes = clean_io.getvalue()

        #randomize filename if toggle is active
        if scramble_filename:
            ext = ".jpg" if save_format.lower() == "jpeg" else f".{save_format.lower()}"
            final_filename = f"sanitized_{uuid.uuid4().hex[:8]}{ext}"
        else:
            base_name = os.path.splitext(file.filename)[0]
            ext = ".jpg" if save_format.lower() == "jpeg" else f".{save_format.lower()}"
            final_filename = f"{base_name}{ext}"

        meta_json = json.dumps(stripped_metadata)
        safe_meta = urllib.parse.quote(meta_json)
        safe_filename = urllib.parse.quote(final_filename)

        headers = {
            "X-Stripped-Metadata": safe_meta,
            "X-Original-Filename": safe_filename,
            "Access-Control-Expose-Headers": "X-Stripped-Metadata, X-Original-Filename",
            "Content-Disposition": f'attachment; filename="{safe_filename}"'
        }

        return Response(content=clean_bytes, media_type=f"image/{save_format.lower()}", headers=headers)

    except UnidentifiedImageError:
        raise HTTPException(status_code=400, detail="Invalid image data.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))