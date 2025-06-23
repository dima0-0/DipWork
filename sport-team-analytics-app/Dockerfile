FROM python:3.11-slim

# Встановлення Poetry
RUN pip install poetry

WORKDIR /app
COPY pyproject.toml poetry.lock ./
RUN poetry install --no-dev

COPY . .
CMD ["poetry", "run", "python", "-m", "app"]
