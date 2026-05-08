FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# The command to start the FastAPI server
CMD ["uvicorn", "sanitizer:app", "--host", "0.0.0.0", "--port", "8000"]