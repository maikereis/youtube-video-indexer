#!/bin/bash
set -e

# Wait for MongoDB to be ready
until mongosh --eval "print('waiting for connection')" &>/dev/null; do
  echo "Waiting for MongoDB to be ready..."
  sleep 2
done

# Create a custom database and user
mongosh <<EOF
use ${MONGO_AUTH}
db.createUser({
  user: "${MONGO_USERNAME}",
  pwd: "${MONGO_PASSWORD}",
  roles: [{ role: "readWrite", db: "${MONGO_NAME}" }]
})
EOF
