FROM python:3.11-bullseye

WORKDIR /app

# Copy the requirements.txt into the container at /app/requirements.txt
COPY requirements_freeze.txt requirements.txt

# Upgrade pip
RUN pip install --upgrade pip

# Install pip packages
RUN pip install -r requirements.txt

COPY src/ src/

COPY static/ static/

COPY templates/ templates/

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "80"]
