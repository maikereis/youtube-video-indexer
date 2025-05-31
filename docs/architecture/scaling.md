## Scalability Design

### Horizontal Scaling
Each service can be scaled independently:

```mermaid
graph LR
    subgraph "Load Balancer"
        LB[Nginx/HAProxy]
    end
    
    subgraph "API Gateway Cluster"
        GW1[Gateway 1]
        GW2[Gateway 2]
        GW3[Gateway N]
    end
    
    subgraph "Queue Worker Cluster"
        QW1[Worker 1]
        QW2[Worker 2]
        QW3[Worker N]
    end
    
    subgraph "Indexing Service Cluster"
        IS1[Indexer 1]
        IS2[Indexer 2]
        IS3[Indexer N]
    end
    
    LB --> GW1
    LB --> GW2
    LB --> GW3
    
    GW1 -.-> QW1
    GW2 -.-> QW2
    GW3 -.-> QW3
    
    QW1 -.-> IS1
    QW2 -.-> IS2
    QW3 -.-> IS3
```

### Performance Characteristics

Based on recent benchmarking:

- **API Gateway**: Handles 245+ RPS with median 1.2s latency
- **Queue Worker**: Processes thousands of messages per minute
- **Indexing Service**: Maintains search indices for millions of documents

### Scaling Strategies

**API Gateway Scaling**:

- Add more instances behind a load balancer
- Optimize for I/O-bound webhook processing
- Scale based on HTTP request volume

**Queue Worker Scaling**:

- Increase worker instances to handle queue backlog
- Monitor queue depth and processing time
- Scale based on notification volume

**Indexing Service Scaling**:

- Scale for write-heavy workloads to MongoDB and Elasticsearch
- Batch operations for improved throughput
- Scale based on indexing latency and volume
