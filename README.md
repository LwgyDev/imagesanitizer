# Image Sanitizer API

A web utility and API designed to strip hidden metadata (EXIF, GPS, device information) from images. Built with FastAPI and Python, the service processes images entirely in memory to prevent data persistence on the server.

## Features

* **In-Memory Processing:** Images are processed using byte buffers and are never written to disk.
* **Selective Metadata Stripping:** Users can configure which metadata to remove and which to keep.
* **Format Support:** Supports JPEG, PNG, WEBP, and Apple's HEIC formats.
* **Security Constraints:** Implements memory-exhaustion protection (decompression bombs) and IP-based rate limiting via `slowapi`.
* **Format Conversion:** Optional conversion to optimized web formats (WEBP, JPEG, PNG).

## Tech Stack

* **Backend:** Python 3.11, FastAPI, Uvicorn
* **Image Processing:** Pillow, pillow-heif
* **Frontend:** Vanilla JavaScript, HTML5, Tailwind CSS
* **Deployment:** Docker, Docker Compose

## Getting Started

You can run this project either using Docker (recommended) or natively with Python.

### Option 1: Run with Docker (Recommended)

This is the fastest way to get the application running without managing local Python environments.

1. Clone the repository:
   ```bash
   git clone [https://github.com/LwgyDev/image-sanitizer.git](https://github.com/LwgyDev/image-sanitizer.git)
   cd image-sanitizer
   ```

2. Start the container:
   ```bash
   docker compose up -d
   ```

3. Open your browser and navigate to `http://localhost:8000`

To stop the application, run `docker compose down`.

### Option 2: Run Natively

If you prefer to run the application directly on your machine without Docker:

1. Clone the repository:
   ```bash
   git clone [https://github.com/LwgyDev/image-sanitizer.git](https://github.com/LwgyDev/image-sanitizer.git)
   cd image-sanitizer
   ```

2. (Optional but recommended) Create and activate a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Start the FastAPI server:
   ```bash
   uvicorn sanitizer:app --host 0.0.0.0 --port 8000
   ```

5. Open your browser and navigate to `http://localhost:8000`

## API Documentation

FastAPI automatically generates API documentation. Once the server is running, you can access the Swagger UI by navigating to:
`http://localhost:8000/docs`