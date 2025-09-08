# AI Video Generator - Akash Network Deployment Guide

## 🚀 Quick Deployment Steps

### 1. Prerequisites
- Docker installed and running
- Docker Hub account
- Akash CLI installed and configured
- AKT tokens for deployment

### 2. Build and Deploy

#### Option A: Use Deployment Script (Recommended)
```bash
# Windows
deploy.bat

# Linux/Mac
chmod +x deploy.sh
./deploy.sh
```

#### Option B: Manual Steps
```bash
# Build Docker image
docker build -t shivapreetham/ai-video-generator:latest .

# Test locally
docker run -p 8000:8000 shivapreetham/ai-video-generator:latest

# Push to Docker Hub
docker login
docker push shivapreetham/ai-video-generator:latest
```

### 3. Update Configuration
1. Edit `akash-docker-deploy.yaml`
2. Update Docker image name if needed
3. Set your API keys:
   - `GEMINI_API_KEY`
   - `ELEVENLABS_API_KEY` 
   - `OPENAI_API_KEY` (optional)

### 4. Deploy to Akash
```bash
# Create deployment
akash tx deployment create akash-docker-deploy.yaml \
  --from <your-wallet-name> \
  --chain-id akashnet-2 \
  --gas-prices 0.025uakt \
  --gas auto \
  --gas-adjustment 1.5

# Check deployment status
akash query deployment get --owner <your-address> --dseq <deployment-sequence>

# Get lease info
akash query market lease list --owner <your-address> --dseq <deployment-sequence>

# Get service URI
akash provider lease-status \
  --from <your-wallet-name> \
  --dseq <deployment-sequence> \
  --provider <provider-address>
```

## 📋 Resource Specifications

- **CPU**: 2.0 cores
- **Memory**: 8GB RAM  
- **Storage**: 20GB persistent storage
- **Network**: Global HTTP access on port 80

## 🔧 API Endpoints

Once deployed, your service will be available at `https://<akash-uri>/`:

- `GET /` - Health check and API info
- `GET /health` - System health status
- `GET /validate-system` - Backend system validation
- `POST /generate-advanced-video` - Advanced video generation
- `POST /generate-advanced-satirical-video` - Satirical video with scraping
- `GET /jobs/{job_id}/status` - Job status monitoring
- `GET /jobs/{job_id}/download` - Download completed videos

## 💰 Cost Estimation

Approximate costs on Akash Network:
- **Resource cost**: ~1500-2000 uAKT per block
- **Monthly estimate**: ~15-20 AKT (depending on usage)

## 🐛 Troubleshooting

### Build Issues
```bash
# Clean Docker cache
docker system prune -a

# Check logs during build
docker build -t test-image . --no-cache
```

### Deployment Issues
```bash
# Check deployment logs
akash provider lease-logs \
  --from <wallet> --dseq <dseq> --provider <provider>

# Check container status
curl https://<akash-uri>/health
```

### Common Problems
1. **Out of memory**: Increase memory allocation in YAML
2. **API key errors**: Verify environment variables in YAML
3. **Timeout errors**: Increase timeout in Dockerfile CMD
4. **Storage issues**: Increase storage allocation

## 🔒 Security Notes

- API keys are set as environment variables
- Container runs as non-root user
- Health checks prevent failed deployments
- Only necessary ports are exposed

## 📊 Monitoring

Monitor your deployment:
- Health endpoint: `/health`
- System validation: `/validate-system`
- Job status: `/jobs/{id}/status`
- Resource usage via Akash provider logs

## 🆘 Support

If you encounter issues:
1. Check the deployment logs
2. Verify API keys are set correctly
3. Ensure sufficient AKT balance
4. Contact Akash Network community for provider issues