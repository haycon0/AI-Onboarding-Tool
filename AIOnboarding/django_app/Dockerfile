# Use an official lightweight Python image.
# https://hub.docker.com/_/python
FROM python:3.14

# Set environment variables
# Prevents Python from writing pyc files to disc
ENV PYTHONDONTWRITEBYTECODE=1
# Prevents Python from buffering stdout and stderr
ENV PYTHONUNBUFFERED=1

# Set the working directory inside the container
WORKDIR /app

# Install system dependencies (optional, but often needed for Postgres/Pillow)
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies\
RUN python -m pip install --upgrade pip
COPY requirements.txt /app/
RUN python -m pip install --no-cache-dir -r requirements.txt

# Copy the Django project code to the container
COPY . /app/