#!/usr/bin/env bash

until docker exec database-heavy-mysql \
  mysqladmin ping -h 127.0.0.1 -u admin -pfrigus7913 --silent; do
  echo "Waiting for MySQL..."
  sleep 1
done

docker exec -i database-heavy-mysql \
  mysql -h 127.0.0.1 -u admin -pfrigus7913 database_heavy <sql/schema.sql
