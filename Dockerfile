FROM python:3.12 as python-base

# Set environment variables
ENV POETRY_VERSION=2.0.1
ENV POETRY_HOME=/opt/poetry
ENV POETRY_VENV=/opt/poetry-venv
ENV FLASK_APP=stonks/app.py

ENV POETRY_CACHE_DIR=/opt/.cache

FROM python-base as poetry-base

# Install poetry
RUN python3 -m venv $POETRY_VENV \
        && $POETRY_VENV/bin/pip install -U pip setuptools \
        && $POETRY_VENV/bin/pip install poetry==$POETRY_VERSION

FROM python-base as stonks

# Copy the virtual environment from the previous image
COPY --from=poetry-base ${POETRY_VENV} ${POETRY_VENV}

ENV PATH="${PATH}:${POETRY_VENV}/bin"

# Set the working directory
WORKDIR /app

# Copy the poetry files
COPY poetry.lock pyproject.toml ./

# Validate the poetry files
RUN poetry check

# Copy the files to the working directory
COPY . /app

# Install the dependencies
RUN poetry install --no-interaction --no-cache

# Expose the port
EXPOSE 5000

# Run the application
CMD ["poetry", "run", "flask", "--app", "stonks.app", "run", "--host=0.0.0.0"]