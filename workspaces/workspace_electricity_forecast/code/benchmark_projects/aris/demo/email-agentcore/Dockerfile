FROM --platform=linux/arm64 python:3.11-slim

WORKDIR /app

# Install deps in smaller layers
COPY requirements.txt .
RUN pip install --no-cache-dir boto3>=1.38.0 pydantic>=2.0
RUN pip install --no-cache-dir strands-agents>=1.13.0 strands-agents-tools>=0.2.0
RUN pip install --no-cache-dir "a2a-sdk[http]>=0.3.0" fastapi>=0.115.0 uvicorn>=0.34.0
RUN pip install --no-cache-dir arise-ai[aws]>=0.1.5 litellm>=1.0

COPY . .

EXPOSE 9000

CMD ["python", "agent.py"]
