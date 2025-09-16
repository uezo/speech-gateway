# Speech Gateway Docker Setup

## Quick Start

### 1. Setup Environment
```bash
cp .env.sample .env
# Edit .env and set your API keys
```

### 2. Create Volume Directories
```bash
./setup-volumes.sh
```

### 3. Start Services
```bash
docker compose up -d
```

## Access

- Application: http://localhost:18000
- PgAdmin: http://localhost:18001

## Configuration

Edit `.env` file to:
- Set API keys (AZURE_API_KEY, OPENAI_API_KEY, etc.)
- Enable/disable services (AZURE_ENABLED=true/false)
- Change ports if needed

## Stop Services

```bash
docker compose down
```
