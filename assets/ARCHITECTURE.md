# YouTube PubSubHubbub Indexer Architecture

This document outlines the architecture for the YouTube PubSubHubbub indexer system, which processes YouTube content notifications, indexes them, and makes them searchable through an API.

## System Overview

The system follows an event-driven microservices architecture, designed to efficiently receive, process, and index YouTube content notifications. The architecture emphasizes scalability, fault tolerance, and separation of concerns.

## Components

### 1. API Gateway Service

This service is responsible for receiving YouTube PubSubHubbub notifications and managing API requests.

**Key Features:**
- Handles webhook verification for PubSubHubbub subscriptions
- Processes incoming notifications and places them in a queue
- Provides a RESTful API for searching and retrieving indexed videos
- Implements rate limiting and trusted host validation
- Exposes statistics and monitoring endpoints

**Technologies:**
- FastAPI framework
- SlowAPI for rate limiting
- Valkey/Redis for queue management

### 2. Queue Worker Service

This service processes notifications from the queue and extracts metadata from YouTube updates.

**Key Features:**
- Dequeues notifications from the message queue
- Parses XML notification data to extract video and channel information
- Performs initial processing and validation
- Forwards enriched metadata to the Indexing Service queue

**Technologies:**
- Asynchronous processing with Python's asyncio
- XML parsing
- Valkey/Redis for queue interaction

### 3. Indexing Service

This service is responsible for storing and indexing video metadata.

**Key Features:**
- Stores video metadata in MongoDB
- Creates and maintains search indices in Elasticsearch
- Updates channel statistics based on video notifications
- Provides data enrichment capabilities

**Technologies:**
- MongoDB for document storage
- Elasticsearch for full-text search capabilities
- Asynchronous processing with Motor and AsyncElasticsearch

### 4. Data Storage Layer

The system uses multiple data stores for different purposes:

**MongoDB:**
- Primary document store
- Stores video and channel metadata
- Supports complex queries and aggregations

**Elasticsearch:**
- Full-text search capabilities
- Fast querying for video content
- Advanced filtering and sorting

**Valkey/Redis:**
- Message queues between services
- Rate limiting data
- Optional caching layer

## Communication Flow

1. YouTube sends a PubSubHubbub notification to the API Gateway
2. API Gateway validates and enqueues the notification
3. Queue Worker dequeues and processes notifications
4. Queue Worker extracts metadata and sends to Indexing Service
5. Indexing Service stores data in MongoDB and indexes in Elasticsearch
6. API clients can query the API Gateway to search and retrieve indexed content

## Scaling Considerations

Each service can be independently scaled:
- API Gateway: Scale to handle increased webhook and API traffic
- Queue Worker: Scale to process more notifications simultaneously
- Indexing Service: Scale to handle higher indexing throughput
- Data Stores: Deploy as clusters when needed for higher loads