#!/bin/sh

if [ "$ENVIRONMENT" = "production" ]; then
    echo "Running in production mode"
    exec poetry run gunicorn -c gunicorn.conf.py
elif [ "$ENVIRONMENT" = "development" ]; then
    echo "Running in development mode"

    echo "Aplicando migrações do banco de dados..."
    poetry run python src/manage.py migrate

    echo "Iniciando o servidor Django..."
    exec poetry run python src/manage.py runserver 0.0.0.0:8000
else
    echo "ENVIRONMENT variable is not set"
    exit 1
fi
