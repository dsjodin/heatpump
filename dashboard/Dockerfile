FROM python:3.11-slim

WORKDIR /app

# Set timezone
ENV TZ=Europe/Stockholm
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Install dependencies
COPY dashboard/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy providers module (shared between collector and dashboard)
COPY providers/ ./providers/

# Copy application files
COPY dashboard/app.py .
COPY dashboard/layout.py .
COPY dashboard/layout_components.py .
COPY dashboard/callbacks_status.py .
COPY dashboard/callbacks_kpi.py .
COPY dashboard/callbacks_graphs.py .
COPY dashboard/config_colors.py .
COPY dashboard/data_query.py .
COPY dashboard/assets/ ./assets/

# Expose port
EXPOSE 8050

# Run the dashboard
CMD ["python", "-u", "app.py"]
