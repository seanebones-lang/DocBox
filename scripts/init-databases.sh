#!/bin/bash
# Initialize databases for DocBox Healthcare System

set -e

echo "Initializing DocBox databases..."

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL..."
until PGPASSWORD=$POSTGRES_PASSWORD psql -h "$POSTGRES_HOST" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c '\q'; do
  >&2 echo "PostgreSQL is unavailable - sleeping"
  sleep 1
done

echo "✓ PostgreSQL is ready"

# Enable pgvector extension
echo "Enabling pgvector extension..."
PGPASSWORD=$POSTGRES_PASSWORD psql -h "$POSTGRES_HOST" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "CREATE EXTENSION IF NOT EXISTS vector;"

echo "✓ pgvector extension enabled"

# Run Alembic migrations
echo "Running database migrations..."
cd backend
alembic upgrade head
cd ..

echo "✓ Migrations complete"

# Initialize Neo4j
echo "Initializing Neo4j constraints..."
python -c "
import asyncio
from backend.graph.neo4j_client import Neo4jClient

async def init():
    client = Neo4jClient()
    await client.verify_connectivity()
    await client.create_indexes()
    await client.close()

asyncio.run(init())
"

echo "✓ Neo4j initialized"

# Initialize Qdrant collection
echo "Initializing Qdrant collection..."
python -c "
import asyncio
from backend.rag.embeddings import EmbeddingService

async def init():
    service = EmbeddingService()
    await service.create_collection('medical_knowledge', vector_size=3072)

asyncio.run(init())
"

echo "✓ Qdrant collection created"

echo ""
echo "========================================="
echo "Database initialization complete!"
echo "========================================="

