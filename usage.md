# Vector Search Project - Usage Guide

A comprehensive guide to all commands and functionality in this IAM Policy Research Agent and Vector Search system.

## 🚀 Quick Start

### Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Set required environment variables
export OPENAI_API_KEY=your_openai_api_key
export PINECONE_API_KEY=your_pinecone_api_key  # Optional for direct Pinecone
```

---

## 🔧 Core Commands

### 1. Start the Vector Search API Server
```bash
# Start the FastAPI backend (runs on http://localhost:8000)
python -m src.api

# Alternative startup
uvicorn src.api:app --host 0.0.0.0 --port 8000

# Check API documentation (when running)
# Visit: http://localhost:8000/docs
```

### 2. IAM Policy Agent (Main Application)
The primary tool for generating AWS IAM policies using vector search + LLM.

#### **Basic Policy Generation**
```bash
# Generate complete IAM policy with auto-save
python examples/iam_policy_agent.py "S3 read access for web application"

# Generate policy for complex scenarios
python examples/iam_policy_agent.py "Lambda function needs DynamoDB read access and CloudWatch logs"

# Generate restrictive policies
python examples/iam_policy_agent.py "Deny all users except security team from accessing confidential S3 bucket"
```

#### **Enhanced Mode Options**
```bash
# Only enhance the prompt (no policy generation)
python examples/iam_policy_agent.py --enhance-only "database permissions"

# Generate policy with additional context
python examples/iam_policy_agent.py --generate-policy "EC2 read access" --context "monitoring application"

# Skip LLM enhancement (vector search only)
python examples/iam_policy_agent.py "S3 policy" --no-llm
```

#### **Save Options**
```bash
# Custom save location
python examples/iam_policy_agent.py "RDS access policy" --save /path/to/policy

# JSON only output
python examples/iam_policy_agent.py "Lambda permissions" --save-format json

# Markdown only output  
python examples/iam_policy_agent.py "S3 policy" --save-format markdown

# Skip auto-save
python examples/iam_policy_agent.py "S3 policy" --no-save
```

#### **Advanced Configuration**
```bash
# Custom API endpoint
python examples/iam_policy_agent.py "S3 policy" --api-base http://custom:8000

# Custom OpenAI key
python examples/iam_policy_agent.py "S3 policy" --openai-key sk-your-key

# Interactive mode (no arguments)
python examples/iam_policy_agent.py
```

### 3. Populate IAM Indexes with AWS Documentation
```bash
# Populate vector databases with AWS IAM documentation from PDF
python populate_iam_indexes.py

# This creates two indexes:
# - iam-policy-guide-fine (400-token chunks for term discovery)
# - iam-policy-guide-context (1200-token chunks for complete examples)
```

---

## 🧪 Testing & Examples

### 4. Test All Vector Store Backends
```bash
# Test Pinecone, Qdrant, and MCP backends
python test_all_backends.py

# Tests functionality across different vector databases
# Shows which backends are properly configured
```

### 5. Test IAM Indexes
```bash
# Test the populated IAM policy indexes
python test_iam_indexes.py

# Verifies that IAM documentation was properly ingested
```

### 6. Test MCP Integration
```bash
# Test Model Context Protocol integration
python test_mcp_integration.py
```

### 7. Run Example Scripts
```bash
# Run all examples (basic + advanced)
python run_examples.py

# Individual examples:
python examples/basic_usage.py      # Basic vector search operations
python examples/advanced_usage.py  # Advanced search features
```

---

## 📊 Vector Search API Endpoints

When the API server is running (`python -m src.api`), you can use these HTTP endpoints:

### **Index Management**
```bash
# Create index
curl -X POST "http://localhost:8000/indexes" \
  -H "Content-Type: application/json" \
  -d '{"name": "my-docs", "dimension": 384}'

# List indexes
curl -X GET "http://localhost:8000/indexes"

# Get index stats
curl -X GET "http://localhost:8000/indexes/my-docs/stats"

# Delete index
curl -X DELETE "http://localhost:8000/indexes/my-docs"
```

### **Document Operations**
```bash
# Add documents
curl -X POST "http://localhost:8000/indexes/my-docs/documents" \
  -H "Content-Type: application/json" \
  -d '[{"id": "1", "text": "Sample document", "metadata": {"category": "test"}}]'

# Batch upload documents
curl -X POST "http://localhost:8000/indexes/my-docs/documents/batch" \
  -H "Content-Type: application/json" \
  -d '{"documents": [...], "batch_size": 100}'
```

### **Search Operations**
```bash
# Semantic search
curl -X POST "http://localhost:8000/indexes/my-docs/search/semantic" \
  -H "Content-Type: application/json" \
  -d '{"query": "sample text", "top_k": 5}'

# Hybrid search
curl -X POST "http://localhost:8000/indexes/my-docs/search/hybrid" \
  -H "Content-Type: application/json" \
  -d '{"query": "sample text", "top_k": 5, "alpha": 0.7}'

# Search with filtering
curl -X POST "http://localhost:8000/indexes/my-docs/search/semantic" \
  -H "Content-Type: application/json" \
  -d '{"query": "sample text", "top_k": 5, "filter": {"category": "test"}}'

# Search with reranking
curl -X POST "http://localhost:8000/indexes/my-docs/search/semantic" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "sample text", 
    "top_k": 10,
    "rerank": {"model": "pinecone-rerank-v0", "topN": 3, "rankFields": ["text"]}
  }'
```

### **Advanced Search**
```bash
# Similarity threshold search
curl -X POST "http://localhost:8000/indexes/my-docs/search/similarity-threshold" \
  -H "Content-Type: application/json" \
  -d '{"query": "sample text", "similarity_threshold": 0.7, "top_k": 5}'

# Cascading search across multiple indexes
curl -X POST "http://localhost:8000/search/cascading" \
  -H "Content-Type: application/json" \
  -d '{
    "indexes": [{"name": "docs1"}, {"name": "docs2"}],
    "query": "sample text",
    "top_k": 10
  }'
```

---

## 🛠️ Configuration & Environment

### Environment Variables
```bash
# Required for LLM features
export OPENAI_API_KEY=sk-your-openai-key

# Vector store backends (choose one or more)
export PINECONE_API_KEY=your-pinecone-key
export PINECONE_ENVIRONMENT=us-east-1

export QDRANT_HOST=localhost
export QDRANT_PORT=6333
export QDRANT_API_KEY=your-qdrant-key

# API configuration
export API_HOST=0.0.0.0
export API_PORT=8000
```

### Vector Store Switching
```bash
# Switch vector store backend via API
curl -X POST "http://localhost:8000/config/switch-store?store_type=pinecone"
curl -X POST "http://localhost:8000/config/switch-store?store_type=qdrant"
curl -X POST "http://localhost:8000/config/switch-store?store_type=pinecone_mcp"
```

---

## 📁 File Structure & Generated Content

### **Generated Policy Files**
IAM policies are auto-saved to `generated_policies/` with timestamps:
```
generated_policies/
├── 20240715_143012_S3_read_access_for_web_application.json
├── 20240715_143012_S3_read_access_for_web_application.md
├── 20240715_144523_Lambda_execution_permissions.json
└── 20240715_144523_Lambda_execution_permissions.md
```

### **Example Files**
- `examples/basic_usage.py` - Basic vector operations
- `examples/advanced_usage.py` - Advanced search features
- `examples/iam_policy_agent.py` - Main IAM policy generator
- `examples/pdf_ingestion.py` - PDF document processing
- `examples/cleanup_data.py` - Data management utilities

---

## 🚀 NEW: Four-Artifact Mode

### **Comprehensive Policy Analysis**
```bash
# Generate all four artifacts with complete analysis
python3 examples/iam_policy_agent.py "S3 read access for web application" --artifacts

# Custom session name and output directory  
python3 examples/iam_policy_agent.py "Lambda permissions" --artifacts \
  --session-name "lambda_demo" --output-dir "production_policies"

# Skip saving (display only)
python3 examples/iam_policy_agent.py "EC2 access" --artifacts --no-save
```

### **What You Get:**
```
outputs/artifacts/session_name/
├── artifacts.json            # Master file with all data
├── read_back.md             # Human-readable summary  
├── spec_dsl.json            # Machine-readable intent
├── baseline_policy.json     # Deterministic policy
├── candidate_policy.json    # LLM-generated policy
├── evidence_archive.json    # RAG context & citations
├── policy_comparison.md     # Side-by-side analysis
├── audit_trail.json         # Confidence & metrics
└── README.md               # Session guide
```

### **Review Results:**
```bash
# Navigate to session directory
cd outputs/artifacts/YYYYMMDD_HHMMSS_session_name

# Quick overview
cat README.md

# Human summary
cat read_back.md

# Policy comparison analysis
cat policy_comparison.md

# Complete data (JSON)
jq . artifacts.json

# Evidence and citations
jq '.rag_context.chunks[0]' evidence_archive.json
```

## 🎯 Common Use Cases

### **1. Generate IAM Policy for New Service**
```bash
python examples/iam_policy_agent.py "Lambda function needs to read from DynamoDB and write CloudWatch logs"
```

### **2. Research IAM Best Practices**
```bash
python examples/iam_policy_agent.py --enhance-only "secure S3 bucket access"
```

### **3. Create Restrictive Security Policy**
```bash
python examples/iam_policy_agent.py "Deny all access to production S3 bucket except for admin role"
```

### **4. Bulk Document Processing**
```bash
# Process and ingest large document collections
python examples/pdf_ingestion.py --pdf-path /path/to/documents/
```

### **5. Health Check & Monitoring**
```bash
# Check system health
curl -X GET "http://localhost:8000/health"

# Monitor specific index performance
curl -X GET "http://localhost:8000/indexes/iam-policy-guide-fine/stats"
```

---

## 🔍 Search Strategies

### **1. Semantic Search**
- Best for: conceptual queries, natural language
- Usage: Finding similar content regardless of exact wording

### **2. Hybrid Search**
- Best for: balanced semantic + keyword matching
- Usage: Most real-world applications
- Alpha parameter: 0.7 = more semantic, 0.3 = more keyword-focused

### **3. Reranking Search**
- Best for: highest quality results
- Usage: When you need the most relevant top-N results

### **4. Cascading Search**
- Best for: searching across multiple document collections
- Usage: Comprehensive search across different knowledge bases

---

## 🚨 Troubleshooting

### **Common Issues**

1. **API Key Missing**
   ```bash
   # Check environment variables
   echo $OPENAI_API_KEY
   echo $PINECONE_API_KEY
   ```

2. **Vector Database Not Available**
   ```bash
   # Test backend connectivity
   python test_all_backends.py
   ```

3. **IAM Indexes Not Populated**
   ```bash
   # Re-populate indexes
   python populate_iam_indexes.py
   ```

4. **API Server Not Running**
   ```bash
   # Start the API server
   python -m src.api
   # Check: http://localhost:8000/docs
   ```

---

## 💡 Tips & Best Practices

1. **Start the API server first** for all vector operations
2. **Use hybrid search** for most real-world queries
3. **Populate IAM indexes** before using the policy agent
4. **Set OpenAI API key** for LLM-enhanced features
5. **Check generated policies** before deploying to production
6. **Use namespaces** to organize different document types
7. **Monitor API health** with `/health` endpoint
8. **Save important policies** with custom names using `--save`

---

This guide covers all major functionality in the vector search system. For the latest API documentation, visit `http://localhost:8000/docs` when the server is running.
