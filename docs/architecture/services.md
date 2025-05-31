## Component Responsibilities

### API Gateway Service
**Primary Role**: HTTP interface and request management

**Key Responsibilities**:

- Accept and validate YouTube PubSubHubbub webhook notifications
- Provide RESTful API endpoints for video search and retrieval
- Implement rate limiting to protect against abuse
- Manage trusted host validation for security
- Queue incoming notifications for processing
- Expose monitoring and statistics endpoints

**Technologies**:

- FastAPI for high-performance async HTTP handling
- SlowAPI for sophisticated rate limiting
- Valkey/Redis for queue management and rate limiting storage

### Queue Worker Service
**Primary Role**: Asynchronous message processing

**Key Responsibilities**:

- Dequeue notification messages from the processing queue
- Parse XML notification payloads to extract metadata
- Validate and channel information
- Forward processed data to the indexing service via queue
- Handle processing errors and implement retry logic

**Technologies**:

- Python asyncio for concurrent message processing
- XML parsing libraries for notification data extraction
- Valkey/Redis client for queue operations

### Indexing Service
**Primary Role**: Data persistence and search indexing

**Key Responsibilities**:

- Store video and channel metadata in MongoDB
- Provide data enrichment through transcript download
- Create and maintain search indices in Elasticsearch
- Update channel statistics based on video notifications
- Manage data consistency across storage systems

**Technologies**:

- Motor (async MongoDB driver) for document operations
- AsyncElasticsearch for search index management
- Python asyncio for concurrent database operations
