## Data Flow Architecture

The system processes data through a series of well-defined stages:

```mermaid
sequenceDiagram
    participant YT as YouTube
    participant GW as API Gateway
    participant NQ as Notification Queue
    participant QW as Queue Worker
    participant MQ as Metadata Queue
    participant IS as Index Service
    participant DB as MongoDB
    participant ES as Elasticsearch
    
    YT->>GW: PubSubHubbub Notification
    GW->>GW: Validate & Authenticate
    GW->>NQ: Enqueue Notification
    GW->>YT: HTTP 200 OK
    
    NQ->>QW: Dequeue Notification
    QW->>QW: Parse XML Data
    QW->>QW: Extract Metadata
    QW->>MQ: Enqueue Metadata

    MQ->>IS: Dequeue Metadata
    IS->>IS: Metadata enrichment
    IS->>DB: Store Video Metadata
    IS->>ES: Update Search Index
    IS->>IS: Update Channel Stats
```

### Processing Stages

1. **Notification Receipt**: YouTube sends PubSubHubbub notifications to the API Gateway
2. **Validation**: The gateway validates the notification signature and source
3. **Queuing**: Valid notifications are queued for asynchronous processing
4. **Extraction**: The Queue Worker parses XML and extracts video metadata
5. **Enrichment**: Additional processing and data validation occurs
6. **Storage**: The Indexing Service persists data to MongoDB
7. **Indexing**: Video metadata is indexed in Elasticsearch for search
8. **Statistics**: Channel-level statistics are updated