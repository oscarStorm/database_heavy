#!/bin/bash
read -p "customer_id: " customer_id
read -p "resource_id: " resource_id
read -p "start_time: " start_time
read -p "end_time: " end_time

curl -X POST http://127.0.0.1:8000/booking \
  -H "Content-Type: application/json" \
  -d "{\"customer_id\": $customer_id, \"resource_id\": $resource_id, \"start_time\": \"$start_time\", \"end_time\": \"$end_time\"}"

