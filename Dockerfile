FROM python:3.12-bookworm

RUN apt-get update && apt-get install -y redis-server supervisor
RUN apt-get clean
RUN rm -rf /var/lib/apt/lists/*

RUN pip install poetry

COPY docker/supervisord.conf /etc/supervisor/conf.d/supervisord.conf
COPY docker/redis.conf /etc/redis/redis.conf

WORKDIR /app

COPY README.md README.md

# Copy the pyproject.toml and poetry.lock file into the container
COPY pyproject.toml poetry.lock ./

# Install project dependencies
RUN poetry config virtualenvs.create true \
&& poetry config virtualenvs.in-project true \
&& poetry install --no-interaction --no-root

COPY src/ src/

COPY static/ static/

COPY templates/ templates/

CMD ["/usr/bin/supervisord"]
