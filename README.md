# IAM Policy Research Agent

An intelligent AWS IAM policy research and generation system that combines vector search with powerful reasoning models (OpenAI o4-mini/o1-mini) to transform vague policy requests into production-ready AWS IAM policies.

## 🎯 **What This Does**

Transform simple requests like *"S3 read access for web application"* into complete, secure IAM policies with:
- **Detailed security considerations** 
- **Specific AWS actions and resources**
- **Production-ready JSON policies**
- **Interactive parameter collection**
- **Automatic policy validation**

## 🚀 **Key Features**

### 🧠 **LLM-Enhanced Policy Generation**
- **Modern OpenAI API**: Uses latest Responses API with `gpt-4.1` and `o4-mini-2025-04-16`
- **Intelligent Prompt Enhancement**: Transforms vague requests into detailed technical specifications
- **Reasoning Models**: Leverages o4-mini for complex policy analysis and generation
- **Interactive Detail Collection**: Prompts users for missing AWS-specific details (account IDs, role names, etc.)

### 📚 **Dual-Index Vector Search**
- **Fine-grained Index**: 400-token chunks for specific AWS concepts and terminology
- **Contextual Index**: 1200-token chunks for complete policy examples and procedures
- **Real AWS Documentation**: Populated with official AWS IAM documentation (PDF ingested)
- **Semantic + Hybrid Search**: Combines meaning-based and keyword-based retrieval

### 🛡️ **Security-First Approach**
- **Least Privilege Principles**: Generates policies following AWS security best practices
- **Automatic Security Conditions**: Includes SecureTransport, VPC restrictions, etc.
- **Policy Validation**: Checks for common security issues and placeholders
- **Production-Ready Output**: Generates policies ready for immediate deployment

### 💾 **User Experience**
- **Auto-Save Functionality**: Saves policies in JSON and Markdown formats with timestamps
- **Clear Confidence Indicators**: Shows AI confidence levels for decisions
- **Complete Explanations**: Provides detailed explanations of what each policy does
- **Improvement Suggestions**: Offers recommendations for enhancing security

## 🏗️ **Architecture**

```
vector_search/
├── examples/
│   └── iam_policy_agent.py      # Main IAM policy research agent
├── src/
│   ├── vector_store/
│   │   ├── base.py              # Vector store abstractions
│   │   ├── pinecone_store.py    # Direct Pinecone integration
│   │   └── pinecone_mcp_store.py # Pinecone MCP integration
│   ├── search_agent.py          # Search orchestration
│   └── api.py                   # REST API endpoints
├── generated_policies/          # Auto-saved policy outputs
└── data/                       # AWS documentation chunks
```

## 🚀 **Quick Start**

### 1. **Setup**

```bash
# Clone and install
git clone <repository-url>
cd vector_search
pip install -r requirements.txt

# Set up OpenAI API key
export OPENAI_API_KEY=your_openai_api_key

# Start the vector search backend
python -m src.api  # Runs on http://localhost:8000
```

### 2. **Generate Your First IAM Policy**

```bash
# Simple usage - generates complete policy with auto-save
python examples/iam_policy_agent.py "S3 read access for web application"

# Enhanced mode - only improve the prompt
python examples/iam_policy_agent.py --enhance-only "database permissions"

# Specific policy generation with context
python examples/iam_policy_agent.py --generate-policy "Lambda execution role" --context "API Gateway integration"
```

### 3. **Interactive Experience**

The agent will:
1. **Enhance your prompt** using AWS documentation context
2. **Generate a complete policy** using reasoning models
3. **Detect missing details** (account IDs, role names, etc.)
4. **Prompt you interactively** to provide real values
5. **Update the policy** with your specific AWS resources
6. **Auto-save** the final policy in multiple formats

Example interaction:
```
🔧 MISSING REQUIRED DETAILS
==================================================
The generated policy contains placeholders that need real AWS values:
  • AWS Account ID
  • IAM Role Name
  • S3 Bucket Name

Would you like to provide these details now? (y/n): y
Enter your AWS Account ID (12 digits): 123456789012
Enter the exact IAM role name: WebAppRole
Enter the S3 bucket name: my-webapp-bucket

✅ Policy updated with your provided details!
```

## 📋 **Usage Examples**

### **Basic Policy Generation**
```bash
python examples/iam_policy_agent.py "EC2 read-only access for monitoring"
```

### **Complex Security Scenarios**
```bash
python examples/iam_policy_agent.py "Deny all users except security team from accessing confidential S3 bucket"
```

### **Custom Options**
```bash
# Save to specific location
python examples/iam_policy_agent.py "RDS access policy" --save /path/to/policy

# JSON only output
python examples/iam_policy_agent.py "Lambda permissions" --save-format json

# Skip auto-save
python examples/iam_policy_agent.py "S3 policy" --no-save
```

## 🧠 **How It Works**

### **1. Prompt Enhancement**
- User provides simple request: *"S3 access for app"*
- Agent searches fine-grained index for AWS concepts
- LLM enhances to detailed specification with specific actions, resources, conditions

### **2. Context Gathering**
- Searches contextual index for complete policy examples
- Retrieves AWS best practices and security considerations
- Ranks and filters most relevant documentation

### **3. Policy Generation**
- Uses reasoning model (o4-mini) for complex policy analysis
- Generates complete JSON policy with explanations
- Includes security notes and improvement suggestions

### **4. Interactive Refinement**
- Detects placeholder values that need real AWS details
- Prompts user for specific account IDs, role names, bucket names
- Updates policy with actual values for production readiness

## 🎛️ **Command Line Options**

```bash
# Basic usage
python examples/iam_policy_agent.py "your request"

# Mode selection
--enhance-only "request"           # Only enhance prompt, no policy generation
--generate-policy "request"        # Generate complete policy

# Output control
--save PATH                        # Custom save path (without extension)
--no-save                         # Skip auto-save
--save-format {json,markdown,both} # Output format (default: both)

# System options
--api-base URL                     # Vector DB API base (default: localhost:8000)
--openai-key KEY                  # OpenAI API key (or use env var)
--no-llm                          # Vector search only, no LLM enhancement
```

## 🔧 **Configuration**

### **Environment Variables**
```bash
# Required for LLM features
OPENAI_API_KEY=sk-your-openai-key

# Optional API configuration
API_HOST=0.0.0.0
API_PORT=8000

# Vector store backend
PINECONE_API_KEY=your-pinecone-key  # If using direct Pinecone
```

### **Model Selection**
The agent automatically selects the best available models:
- **Prompt Enhancement**: `gpt-4.1` (excellent instruction following)
- **Policy Generation**: `o4-mini-2025-04-16` (reasoning model for complex analysis)
- **Fallbacks**: `gpt-4o`, `gpt-4-turbo` if reasoning models unavailable

## 📊 **Sample Output**

### **Input**
```bash
python examples/iam_policy_agent.py "S3 read access for web application"
```

### **Output**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "S3ReadOnlyAccess",
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:ListBucket",
        "s3:GetBucketLocation"
      ],
      "Resource": [
        "arn:aws:s3:::my-webapp-bucket",
        "arn:aws:s3:::my-webapp-bucket/*"
      ],
      "Condition": {
        "Bool": {
          "aws:SecureTransport": "true"
        }
      }
    }
  ]
}
```

Plus comprehensive explanation, security notes, and improvement suggestions.

## 🗂️ **Auto-Generated Files**

The agent automatically saves policies in `generated_policies/` with timestamps:

```
generated_policies/
├── 20240715_143012_S3_read_access_for_web_application.json
├── 20240715_143012_S3_read_access_for_web_application.md
├── 20240715_144523_Lambda_execution_permissions.json
└── 20240715_144523_Lambda_execution_permissions.md
```

## 🧪 **Data Sources**

The system uses real AWS documentation:
- **IAM User Guide** (official AWS PDF documentation)
- **Fine-grained chunks**: Specific AWS concepts, actions, conditions
- **Contextual chunks**: Complete policy examples, procedures, tutorials
- **Continuously updated**: Easy to add new AWS documentation

## 🔍 **Vector Search API**

For direct vector search without LLM enhancement:

```bash
# Semantic search
curl -X POST "http://localhost:8000/indexes/iam-policy-guide-fine/search/semantic" \
     -H "Content-Type: application/json" \
     -d '{"query": "S3 permissions", "top_k": 5, "namespace": "aws-iam-detailed"}'

# Hybrid search with reranking
curl -X POST "http://localhost:8000/indexes/iam-policy-guide-context/search/semantic" \
     -H "Content-Type: application/json" \
     -d '{
       "query": "policy examples bucket access",
       "top_k": 10,
       "namespace": "aws-iam-examples",
       "rerank": {"model": "pinecone-rerank-v0", "topN": 3, "rankFields": ["text"]}
     }'
```

## 🛡️ **Security Best Practices**

The agent follows AWS security principles:
- **Least Privilege**: Grants minimum necessary permissions
- **Explicit Deny**: Uses deny statements where appropriate
- **Condition Keys**: Includes security conditions (SecureTransport, MFA, etc.)
- **Resource Specificity**: Avoids wildcards unless necessary
- **Documentation**: Explains security implications of each policy

## 🤝 **Contributing**

1. **Add new AWS documentation**: Place PDFs in `data/` and run ingestion
2. **Improve prompts**: Enhance the LLM prompts in `iam_policy_agent.py`
3. **Add policy templates**: Extend the vector search with new policy patterns
4. **Test with real scenarios**: Validate against actual AWS use cases

## 🚨 **Important Notes**

- **Review generated policies** before deploying to production
- **Test policies** in development environments first
- **Keep documentation updated** as AWS introduces new services
- **Monitor OpenAI usage** as LLM calls incur API costs
- **Validate account-specific details** (account IDs, role names, etc.)

## 📖 **Examples Gallery**

### **Simple S3 Access**
```bash
Input: "S3 read access for web app"
Output: Complete policy with GetObject, ListBucket, SecureTransport condition
```

### **Complex Security Scenario**
```bash
Input: "Deny all users except security team from confidential bucket"
Output: Bucket policy with NotPrincipal exceptions and explicit deny
```

### **Cross-Service Permissions**
```bash
Input: "Lambda function needs to read from DynamoDB and write logs"
Output: Multi-service policy with appropriate CloudWatch and DynamoDB permissions
```

## 🎓 **Learning Resources**

- **AWS IAM Documentation**: https://docs.aws.amazon.com/iam/
- **Policy Examples**: Check `generated_policies/` for real outputs
- **Vector Search**: Explore the search API for understanding how retrieval works
- **OpenAI Reasoning Models**: Learn about o4-mini capabilities

## 📞 **Support**

- **Issues**: Open GitHub issues for bugs or feature requests
- **Documentation**: Check the `examples/` directory for usage patterns
- **API Reference**: Visit `http://localhost:8000/docs` when running the API
- **Vector Search**: Use the search endpoints to understand document retrieval

---

**Transform your IAM policy requirements into production-ready AWS policies with AI-powered assistance!** 🚀 