# Use an official Python runtime as a base image
FROM python:3.12

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY main.py websocket_server.py gpt_memory.py flask_app.py run.py

# Expose the Flask port
EXPOSE 5000

# Start your application (runs both Flask + WebSocket if you use threading inside main)
CMD ["python", "main.py"]
