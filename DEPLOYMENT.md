# AI Video Generator - Production Deployment Guide

## Overview

This guide covers deploying your AI video generator backend service to Akash Network using Docker containers. The deployment includes advanced video generation capabilities with multi-API key fallback, satirical content generation, and efficient resource management.

## Prerequisites

### 1. Environment Setup
- Docker installed and configured
- Akash CLI installed
- Docker Hub account (or alternative registry)
- Akash wallet with sufficient AKT tokens

### 2. API Keys Required
- **Gemini API Key**: For script generation (`GEMINI_API_KEY`)
- **ElevenLabs API Keys**: 3 keys for fallback system (`ELEVENLABS_API_KEY_1`, `ELEVENLABS_API_KEY_2`, `ELEVENLABS_API_KEY_3`)
- **OpenAI API Key**: Optional, for advanced features (`OPENAI_API_KEY`)

## Deployment Steps

### Step 1: Prepare Environment Variables

Create your environment configuration by editing the SDL file:

```bash
# Replace placeholder API keys in akash-docker-deploy.yaml
vim akash-docker-deploy.yaml
```

Update these environment variables:
- `GEMINI_API_KEY=your_actual_gemini_key`
- `ELEVENLABS_API_KEY_1=your_primary_elevenlabs_key`
- `ELEVENLABS_API_KEY_2=your_backup_key_1`
- `ELEVENLABS_API_KEY_3=your_backup_key_2`
- `OPENAI_API_KEY=your_openai_key` (optional)

### Step 2: Build and Push Docker Image

```bash
# Build optimized production image
docker build -t shivapreetham/ai-video-generator:v2.0 .

# Test locally (optional)
docker run -p 8000:8000 --env-file .env shivapreetham/ai-video-generator:v2.0

# Push to Docker Hub
docker push shivapreetham/ai-video-generator:v2.0
```

### Step 3: Deploy to Akash Network

```bash
# Set up Akash environment variables
export AKASH_KEY_NAME="your-key-name"
export AKASH_ACCOUNT_ADDRESS="your-akash-address"

# Create deployment
akash tx deployment create akash-docker-deploy.yaml \
  --from $AKASH_KEY_NAME \
  --gas-prices 0.025uakt \
  --gas auto \
  --gas-adjustment 1.5

# Check deployment status
akash query deployment list --owner $AKASH_ACCOUNT_ADDRESS

# Get bids (wait a moment for providers to respond)
akash query market bid list --owner $AKASH_ACCOUNT_ADDRESS

# Accept a lease (replace DSEQ, GSEQ, OSEQ, PROVIDER)
akash tx market lease create \
  --dseq $DSEQ \
  --gseq $GSEQ \
  --oseq $OSEQ \
  --provider $PROVIDER \
  --from $AKASH_KEY_NAME \
  --gas-prices 0.025uakt \
  --gas auto \
  --gas-adjustment 1.5

# Get service status and URI
akash provider lease-status \
  --dseq $DSEQ \
  --provider $PROVIDER \
  --from $AKASH_KEY_NAME
```

## Resource Configuration

### Current Allocation
- **CPU**: 4 cores (optimized for video processing)
- **RAM**: 12GB (handles large video/image operations)
- **Storage**: 50GB persistent (outputs and temporary files)
- **Estimated Cost**: 30-50 AKT/month

### Resource Optimization Options

#### Light Configuration (Cost-optimized)
```yaml
resources:
  cpu:
    units: 2.0     # 2 cores
  memory:
    size: 6Gi      # 6GB RAM
  storage:
    - size: 20Gi   # 20GB storage
```
**Estimated Cost**: 15-25 AKT/month

#### High-Performance Configuration
```yaml
resources:
  cpu:
    units: 8.0     # 8 cores
  memory:
    size: 24Gi     # 24GB RAM
  storage:
    - size: 100Gi  # 100GB storage
```
**Estimated Cost**: 80-120 AKT/month

## API Endpoints

Once deployed, your service will expose these endpoints:

### Core Video Generation
- `POST /generate-advanced-video` - Advanced video generation with full pipeline
- `POST /generate-video` - Legacy video generation
- `GET /jobs/{job_id}/status` - Check generation status
- `GET /jobs/{job_id}/download` - Download generated video

### Satirical Content
- `POST /generate-advanced-satirical-video` - Advanced satirical video generation
- `POST /generate-satirical-video` - Standard satirical video generation
- `GET /fetch-daily-mash-content` - Get available satirical content

### System & Health
- `GET /health` - Health check endpoint
- `GET /api` - Service information
- `GET /validate-system` - System validation
- `POST /cleanup` - Manual cleanup trigger

## Monitoring & Maintenance

### Health Monitoring
The deployment includes automatic health checks:
- **Health Check Interval**: 30 seconds
- **Timeout**: 30 seconds
- **Start Period**: 120 seconds (allows for initialization)
- **Retries**: 3 attempts

### Log Access
```bash
# Get logs from your deployment
akash provider lease-logs \
  --dseq $DSEQ \
  --provider $PROVIDER \
  --from $AKASH_KEY_NAME
```

### Storage Cleanup
The service includes automatic cleanup:
- **Cleanup Interval**: 6 hours
- **Max Storage**: 15GB
- **Manual Cleanup**: Available via `/cleanup` endpoint

### Performance Monitoring
Monitor key metrics:
- CPU usage (should stay under 80% average)
- Memory usage (should stay under 10GB average)
- Storage usage (monitored and cleaned automatically)
- API response times
- Generation success rates

## Security Considerations

### API Key Management
- Never commit API keys to version control
- Use Akash SDL environment variables
- Rotate API keys regularly
- Monitor API usage for anomalies

### Network Security
- Service exposes only port 80 (mapped from 8000)
- All communication over HTTPS when using proper domains
- No SSH access required

### Container Security
- Runs as non-root user (`appuser`)
- Minimal attack surface with slim base image
- Regular security updates via image rebuilds

## Troubleshooting

### Common Issues

#### 1. Deployment Fails
```bash
# Check deployment events
akash query deployment get --dseq $DSEQ --owner $AKASH_ACCOUNT_ADDRESS

# Verify SDL syntax
akash validate akash-docker-deploy.yaml
```

#### 2. No Bids Received
- Check pricing (may need to increase `amount` in SDL)
- Verify provider attributes requirements
- Check for provider capacity issues

#### 3. Service Health Check Fails
```bash
# Check logs
akash provider lease-logs --dseq $DSEQ --provider $PROVIDER --from $AKASH_KEY_NAME

# Common issues:
# - Missing environment variables
# - API key issues
# - Insufficient resources
```

#### 4. API Generation Failures
- Verify all API keys are valid and have sufficient credits
- Check network connectivity to external APIs
- Monitor rate limiting and adjust accordingly

### Performance Optimization

#### 1. Worker Configuration
Adjust Gunicorn workers based on resource allocation:
- **2 cores**: 2-3 workers
- **4 cores**: 3-5 workers  
- **8 cores**: 5-8 workers

#### 2. Memory Optimization
- Monitor memory usage patterns
- Adjust cleanup intervals for optimal balance
- Consider increasing memory for large video processing

#### 3. Storage Management
- Monitor storage usage
- Adjust cleanup policies based on usage patterns
- Consider persistent storage for better performance

## Scaling Considerations

### Horizontal Scaling
For high load, deploy multiple instances:
```yaml
deployment:
  ai-video-generator:
    akash-network:
      profile: ai-video-service
      count: 3  # Multiple instances
```

### Load Balancing
Implement load balancing at the application level:
- Job queue system
- Database-backed job persistence
- Shared storage for outputs

## Cost Analysis

### Monthly Estimates (USD equivalent)
- **Light**: $5-15/month
- **Standard**: $15-35/month  
- **High-Performance**: $40-80/month

### Cost Optimization Tips
1. Use cleanup policies to minimize storage
2. Scale down during off-peak hours
3. Monitor and optimize resource usage
4. Use appropriate pricing in SDL

## Support & Updates

### Regular Maintenance
- Update Docker image monthly
- Monitor security advisories
- Update dependencies regularly
- Review and optimize resource allocation

### Updates Deployment
```bash
# Build new version
docker build -t shivapreetham/ai-video-generator:v2.1 .
docker push shivapreetham/ai-video-generator:v2.1

# Update SDL with new image tag
# Redeploy with updated configuration
```

This deployment configuration provides a robust, scalable, and cost-effective solution for hosting your AI video generation service on Akash Network.