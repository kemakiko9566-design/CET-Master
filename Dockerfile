FROM python:3.10-slim

WORKDIR /app

# Copy Python dependencies and install (use mirror for faster download in China)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt --default-timeout=120 -i https://mirrors.aliyun.com/pypi/simple/

# Copy application code
COPY agent_a_api.py agent_a_processor.py app.py ./

# Expose ports
EXPOSE 8000 8001

CMD ["sh", "-c", "python agent_a_api.py & python app.py & wait"]
