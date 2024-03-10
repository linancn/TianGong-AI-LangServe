FROM python:3.12-bookworm

RUN apt-get update && apt-get install -y redis-server supervisor
RUN apt-get clean
RUN rm -rf /var/lib/apt/lists/*

COPY docker/supervisord.conf /etc/supervisor/conf.d/supervisord.conf
COPY docker/redis.conf /etc/redis/redis.conf

WORKDIR /app

# Copy the requirements.txt into the container at /app/requirements.txt
COPY requirements.txt requirements.txt

# Upgrade pip
RUN pip install --upgrade pip

# Install pip packages
RUN pip install -r requirements.txt

COPY src/ src/

COPY static/ static/

COPY templates/ templates/

CMD ["/usr/bin/supervisord"]
