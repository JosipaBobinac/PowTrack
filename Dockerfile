FROM python:3.9-slim

WORKDIR /app/backend

COPY requirements.txt /app/backend/requirements.txt
RUN pip install -r /app/backend/requirements.txt

COPY backend /app/backend

ENV FLASK_APP=application.py

CMD ["flask", "run", "--host=0.0.0.0", "--port=8080"]

