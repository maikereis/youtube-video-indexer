# System Architecture Overview

The YouTube Video Indexer follows an event-driven, microservices architecture designed for high scalability, fault tolerance, and maintainability. This document provides a comprehensive overview of the system's design principles and architectural decisions.

## Design Principles

### Event-Driven Architecture
The system is built around asynchronous message passing, allowing services to operate independently while maintaining loose coupling. This approach provides several benefits:

- **Scalability**: Each service can be scaled independently based on demand
- **Resilience**: Failures in one service don't cascade to others
- **Flexibility**: New services can be added without modifying existing ones
- **Performance**: Non-blocking operations maximize throughput

### Separation of Concerns
Each service has a single, well-defined responsibility:

- **API Gateway**: HTTP interface and request routing
- **Queue Worker**: Message processing and data extraction
- **Indexing Service**: Data persistence and search indexing

### Fault Tolerance
The system implements multiple layers of fault tolerance:

- **Queue-based Processing**: Messages persist even if services are temporarily unavailable
- **Retry Logic**: Failed operations are automatically retried with exponential backoff
- **Circuit Breakers**: Prevent cascading failures by temporarily disabling unhealthy dependencies
- **Health Checks**: Monitor service availability and trigger alerts

## High-Level Architecture

```mermaid
graph TB
   subgraph "External"
       YT[YouTube PubSubHubbub]
       CLIENT[API Clients]
   end
   
   subgraph "API Layer"
       GW[API Gateway<br/>FastAPI + SlowAPI]
   end
   
   subgraph "Processing Layer"
       QW[Queue Worker<br/>Async Python]
       IS[Indexing Service<br/>Motor + AsyncES]
   end
   
   subgraph "Data Layer"
       REDIS[(Valkey/Redis<br/>Queues + Cache)]
       MONGO[(MongoDB<br/>Document Store)]
       ES[(Elasticsearch<br/>Search Index)]
   end
   
   YT -->|Webhook| GW
   CLIENT -->|HTTP API| GW
   GW <-->|Queue Operations| REDIS
   GW -->|Enqueue| QW
   QW <-->|Queue Operations| REDIS
   QW -->|Process| IS
   IS -->|Store| MONGO
   IS -->|Index| ES
   
   style YT fill:#e8f4f8,stroke:#2c3e50,stroke-width:2px
   style CLIENT fill:#f0f8e8,stroke:#2c3e50,stroke-width:2px
   style GW fill:#f8f0e8,stroke:#2c3e50,stroke-width:2px
   style QW fill:#e8e8f8,stroke:#2c3e50,stroke-width:2px
   style IS fill:#f8e8f0,stroke:#2c3e50,stroke-width:2px
   style REDIS fill:#e8f8f0,stroke:#2c3e50,stroke-width:2px
   style MONGO fill:#f8f8e8,stroke:#2c3e50,stroke-width:2px
   style ES fill:#f4f0f8,stroke:#2c3e50,stroke-width:2px
```
