#!/bin/bash
read -p "capacity: " capacity
read -p "tablename: " tablename
read -p "Active (true/false): " active

curl -X POST http://127.0.0.1:8000/resources \
  -H "Content-Type: application/json" \
  -d "{\"capacity\": \"$capacity\",\"tablename\": \"$tablename\", \"active\": $active}"

