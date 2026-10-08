#!/bin/bash
set -e

POSTGRES_NON_ROOT_PASSWORD=$(cat /run/secrets/non_root_password | tr -d '\r\n')

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE USER ${POSTGRES_NON_ROOT_USER} WITH PASSWORD '${POSTGRES_NON_ROOT_PASSWORD}';
EOSQL