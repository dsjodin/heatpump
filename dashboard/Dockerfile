FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY app.py .
COPY layout.py .
COPY layout_components.py .
COPY callbacks_status.py .
COPY callbacks_kpi.py .
COPY callbacks_graphs.py .
COPY config_colors.py .
COPY data_query.py .
COPY assets/ ./assets/

# Expose port
EXPOSE 8050

# Run the dashboard
CMD ["python", "-u", "app.py"]
