FROM python:3.11-slim

WORKDIR /loader
RUN pip install --no-cache-dir pandas seaborn pymysql cryptography sqlalchemy
COPY loader.py .
CMD ["python", "loader.py"]