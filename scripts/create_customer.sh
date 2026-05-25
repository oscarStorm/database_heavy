#!/usr/bin/env bash

curl -X POST http://127.0.0.1:8000/customers \
  -H "Content-Type: application/json" \
  -d '{"name": "Oscar", "email": "oscar@example.com"}'

