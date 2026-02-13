FROM python:3.9-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code + teammate code
COPY uplink_server.py /app/
COPY connect4.py /app/

# Copy model files into the container
COPY models /models
ENV MODEL_DIR=/models

ENV PYTHONUNBUFFERED=1

CMD ["python", "uplink_server.py"]