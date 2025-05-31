# Installation Guide

This guide will walk you through setting up the YouTube Video Indexer system on your local development environment or production server.

## Prerequisites

### Software Dependencies

#### Required Software
- **python**: 3.12+
- **docker engine**: Docker version 28.1.1, build 4eba377
- **docker compose**: Docker Compose v2.35.1
- **git**: For source code management
- **uv**: astral-uv package manager

## Installation Methods

### Method 1: Docker Compose (Recommended)

This is the fastest way to get the system running with all dependencies.

#### Step 1: Clone the Repository
```bash
git clone https://github.com/maikereis/youtube-video-indexer.git
cd youtube-video-indexer
```

#### Step 2: Configure Environment
```bash
# Copy environment template
cp .env.example .env

# Edit configuration (see Configuration section below)
nano .env
```

#### Step 3: Start Services
```bash
# Start all services in background
docker compose up -d

# View logs
docker compose logs -f
```

#### Step 4: Verify Installation
```bash
# Check service health
curl http://localhost:8080/api/v1/health/

# Expected response
{"name":"YouTube Indexer API","version":"1.0.0","status":"online","docs":"/docs"}
```

### Method 2: Development Setup

For contributors and developers.

#### Step 1: Fork and Clone
```bash
# Fork the repository on GitHub, then:
git clone https://github.com/YOUR_USERNAME/youtube-video-indexer.git
cd youtube-video-indexer

# Add upstream remote
git remote add upstream https://github.com/maikereis/youtube-video-indexer.git
```

#### Step 2: Install Development Dependencies
```bash
# Create development environment
uv sync

# Install with development dependencies
uv sync --dev

# Install pre-commit hooks
pre-commit install
```

#### Step 3: Run Tests
```bash
# Run test suite
pytest
```
