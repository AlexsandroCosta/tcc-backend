FROM python:3.10.19-slim-bookworm AS base

ENV POETRY_HOME=/opt/poetry
ENV PATH=${POETRY_HOME}/bin:${PATH}

RUN apt-get update \
    && apt-get install --no-install-recommends -y \
    curl \
    libgl1 \
    libglib2.0-0 \
    tesseract-ocr \
    tesseract-ocr-por \
    liblouis-bin \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*


RUN curl -sSL https://install.python-poetry.org | python3 - && poetry --version

FROM base AS builder

WORKDIR /app
COPY poetry.lock pyproject.toml ./
RUN poetry config virtualenvs.in-project true
RUN poetry install --only main --no-root --no-interaction

FROM base AS runner

WORKDIR /app
COPY --from=builder /app/.venv/ /app/.venv/

COPY . /app

EXPOSE 8000

RUN chmod +x /app/entrypoint.sh

FROM runner AS development

WORKDIR /app
ENTRYPOINT [ "/app/entrypoint.sh" ]

FROM runner AS production

# Set user and group
ARG user=django
ARG group=django
ARG uid=1000
ARG gid=1000
RUN groupadd -g ${gid} ${group}
RUN useradd -u ${uid} -g ${group} -s /bin/sh -m ${user}

# Switch to user
RUN chown -R ${uid}:${gid} /app

USER ${uid}:${gid}

WORKDIR /app
ENTRYPOINT [ "/app/entrypoint.sh" ]