FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy simulator code
COPY . /app/simulator/

# Copy config (will be mounted as volume in production)
COPY ../config.yaml /app/config.yaml

# Run simulator
CMD ["python", "-u", "simulator/simulator.py"]
