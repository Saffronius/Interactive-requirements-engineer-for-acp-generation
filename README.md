# IAM Policy Research Agent - Four-Artifact Architecture

An intelligent AWS IAM policy research and generation system that combines vector search with powerful reasoning models to transform vague policy requests into production-ready AWS IAM policies with complete auditability and traceability.

## 🎯 **What This Does**

Transform simple requests like *"S3 read access for web application"* into **four comprehensive artifacts**:

1. **📖 ReadBack**: Human-readable summary with assumptions and risks
2. **🏗️ SpecDSL**: Machine-readable intent with evidence citations  
3. **⚙️ Baseline Policy**: Deterministic IAM policy from canonizer rules
4. **🧠 Candidate Policy**: LLM-generated policy for comparison

Each generation includes complete provenance, confidence scores, and automated risk assessment.

## 🚀 **Key Features**

### 🏗️ **Four-Artifact Architecture**
- **Intent Extraction**: Structured intent with evidence from AWS documentation
- **Deterministic Baseline**: Always have a safe policy to ship
- **LLM Enhancement**: Intelligent policy generation with reasoning models  
- **Comprehensive Analysis**: Side-by-side comparison and risk assessment

### 🧠 **LLM-Enhanced Generation**
- **Modern OpenAI API**: Uses `gpt-4.1` for enhancement and `o4-mini-2025-04-16` for reasoning
- **Intelligent Intent Extraction**: Transforms vague requests into structured specifications
- **Evidence-Based**: Every decision backed by AWS documentation citations
- **Confidence Scoring**: Know when manual review is needed

### 📚 **Dual-Index Vector Search**
- **Fine-grained Index**: 400-token chunks for specific AWS concepts and terminology
- **Contextual Index**: 1200-token chunks for complete policy examples and procedures
- **Real AWS Documentation**: Populated with official AWS IAM User Guide
- **Semantic + Hybrid Search**: Combines meaning-based and keyword-based retrieval

### 🛡️ **Security & Auditability**
- **Evidence Tracking**: Full provenance from prompt to policy with documentation citations
- **Validation Rules**: Enforced security patterns and best practices
- **Comparison Analysis**: Automated assessment of baseline vs candidate policies
- **Audit Trails**: Complete session history with confidence metrics

### 💾 **Structured Output**
- **Session Management**: Organized artifact storage with global indexing
- **Multiple Formats**: JSON for automation, Markdown for humans
- **Comprehensive Reports**: Policy comparison, evidence archives, audit trails
- **Easy Navigation**: Auto-generated README and session guides

## 🏗️ **Architecture**

```
vector_search/
├── src/
│   ├── policy_types.py          # Data contracts and validation
│   ├── intent_extractor.py      # NL → SpecDSL with evidence
│   ├── canonizer.py             # SpecDSL → deterministic policy
│   ├── artifact_saver.py        # Comprehensive storage system
│   ├── search_agent.py          # Vector search coordination
│   └── vector_store/            # Backend abstractions
├── examples/
│   ├── iam_policy_agent.py      # Main four-artifact generator
│   ├── pdf_ingestion.py         # Process new AWS documentation
│   └── CHUNKING_STRATEGY.md     # Documentation approach
├── populate_iam_indexes.py      # Setup AWS documentation indexes
└── outputs/                     # Generated artifacts
    ├── artifacts/               # Four-artifact sessions
    ├── session_index.json       # Global session tracker
    └── ...
```

## 🚀 **Quick Start**

### 1. **Setup**

```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment
export OPENAI_API_KEY=your_openai_api_key

# Start the vector search backend
python3 -m src.api  # Runs on http://localhost:8000
```

### 2. **Populate IAM Documentation (One-time)**

```bash
# Download AWS IAM User Guide PDF and populate vector indexes
python3 populate_iam_indexes.py
```

### 3. **Generate Your First Policy Artifacts**

```bash
# Four-artifact mode with comprehensive analysis
python3 examples/iam_policy_agent.py "S3 read access for web application" --artifacts

# Custom session name and output location
python3 examples/iam_policy_agent.py "Lambda execution role" --artifacts \
  --session-name "lambda_prod_policy" --output-dir "production_policies"
```

### 4. **Review Generated Artifacts**

```bash
# Navigate to session directory
cd outputs/artifacts/YYYYMMDD_HHMMSS_session_name

# Quick overview
cat README.md

# Human-readable summary
cat read_back.md

# Policy comparison analysis  
cat policy_comparison.md

# Complete structured data
jq . artifacts.json
```

## 📋 **Output Structure**

Each generation creates a complete session directory:

```
outputs/artifacts/session_name/
├── artifacts.json            # Master file with all artifacts and metadata
├── read_back.md             # Human-readable summary and risk analysis
├── spec_dsl.json            # Machine-readable intent with evidence
├── baseline_policy.json     # Deterministic policy from canonizer
├── candidate_policy.json    # LLM-generated policy
├── evidence_archive.json    # RAG context and documentation citations
├── policy_comparison.md     # Side-by-side policy analysis
├── audit_trail.json         # Confidence scores and quality metrics
└── README.md               # Session overview and usage guide
```

## 💡 **Usage Examples**

### **Basic Policy Generation**
```bash
python3 examples/iam_policy_agent.py "EC2 read-only access for monitoring" --artifacts
```

### **Complex Security Scenarios**
```bash
python3 examples/iam_policy_agent.py "Cross-account S3 access with MFA requirement" --artifacts
```

### **Production Workflow**
```bash
# Generate with custom naming
python3 examples/iam_policy_agent.py "Production RDS access policy" --artifacts \
  --session-name "prod_rds_v1" --output-dir "approved_policies"

# Review and validate
cd approved_policies/artifacts/prod_rds_v1
cat policy_comparison.md  # Check baseline vs candidate alignment
cat audit_trail.json     # Verify confidence scores

# Deploy the safer baseline or validated candidate
aws iam create-policy --policy-name ProdRDSAccess \
  --policy-document file://baseline_policy.json
```

## 🔧 **Command Reference**

### **Four-Artifact Mode (Recommended)**
```bash
# Basic generation
python3 examples/iam_policy_agent.py "your request" --artifacts

# Customized output
python3 examples/iam_policy_agent.py "your request" --artifacts \
  --session-name "custom_name" \
  --output-dir "custom_directory" \
  --no-save  # Display only, no files

# API configuration
python3 examples/iam_policy_agent.py "your request" --artifacts \
  --api-base http://localhost:8000 \
  --openai-key sk-your-key
```

### **Legacy Mode (Single Policy)**
```bash
# For compatibility with existing workflows
python3 examples/iam_policy_agent.py "your request"
python3 examples/iam_policy_agent.py "your request" --save-format json
```

## 🧠 **How It Works**

### **1. Intent Extraction**
- Searches fine-grained AWS documentation chunks
- Uses LLM to extract structured intent with evidence
- Produces human-readable ReadBack and machine-readable SpecDSL

### **2. Baseline Generation**  
- Applies deterministic canonizer rules to SpecDSL
- Generates safe, idiomatic IAM policies
- Enforces security patterns and validation rules

### **3. Candidate Generation**
- Uses reasoning models (o4-mini) with contextual documentation
- Generates comprehensive policies with explanations
- Provides security notes and improvement suggestions

### **4. Analysis & Storage**
- Compares baseline vs candidate policies automatically
- Archives complete RAG context and evidence citations
- Tracks confidence scores and quality metrics
- Organizes everything in structured session directories

## 🛡️ **Security & Best Practices**

### **Built-in Security**
- **Least Privilege**: Default to minimal necessary permissions
- **Explicit Denials**: Automatic security restrictions
- **Condition Enforcement**: SecureTransport, IP restrictions, VPC requirements
- **Validation Rules**: Prevent dangerous patterns

### **Audit & Compliance**
- **Complete Provenance**: Every decision traced to documentation
- **Confidence Scoring**: Quantified reliability metrics  
- **Evidence Archives**: Full context preservation
- **Session History**: Global tracking of all generations

### **Production Deployment**
1. **Review ReadBack** for human understanding
2. **Check Comparison Report** for policy alignment
3. **Validate Confidence Scores** (>80% recommended)
4. **Deploy Baseline** for safety or **Candidate** if validated
5. **Monitor with CloudTrail** and **test in development first**

## 📊 **Data Sources**

- **AWS IAM User Guide**: Official AWS PDF documentation
- **Fine-grained Chunks**: 400-token pieces for concept discovery
- **Contextual Chunks**: 1200-token pieces for complete examples
- **Evidence Citations**: Full traceability to source documentation

## 🔧 **Setup & Administration**

### **Adding New Documentation**
```bash
# Process new AWS PDFs
python3 examples/pdf_ingestion.py --pdf-path /path/to/new-guide.pdf

# Update existing indexes
python3 populate_iam_indexes.py
```

### **Health Monitoring**
```bash
# Check vector database health
curl -X GET "http://localhost:8000/health"

# Verify IAM indexes
python3 test_iam_indexes.py
```

### **Session Management**
```bash
# View all sessions
jq '.sessions' outputs/session_index.json

# Find sessions by confidence
jq '.sessions[] | select(.extraction_confidence > 0.9)' outputs/session_index.json
```

## 📈 **Benefits Over Traditional IAM Policy Generation**

### **Traditional Approach:**
- ❌ Single policy output with no comparison
- ❌ No provenance or evidence tracking  
- ❌ Manual security review required
- ❌ No confidence indicators
- ❌ Difficult to audit decisions

### **Four-Artifact Approach:**
- ✅ **Two policies**: Safe baseline + enhanced candidate
- ✅ **Complete provenance**: Every decision traced to documentation
- ✅ **Automated analysis**: Risk assessment and comparison reports
- ✅ **Confidence scoring**: Know when manual review is needed
- ✅ **Audit ready**: Full session history and evidence archives

## 🚨 **Important Notes**

- **Review all policies** before production deployment
- **Test in development** environments first
- **Monitor confidence scores** - manual review if <80%
- **Keep documentation updated** as AWS services evolve
- **Validate account-specific details** (account IDs, resource names)

## 🤝 **Contributing**

1. **Add AWS Documentation**: Place new PDFs in appropriate locations
2. **Extend Canonizer Rules**: Add support for new AWS services
3. **Improve Intent Extraction**: Enhance LLM prompts and validation
4. **Add Policy Patterns**: Contribute common policy templates

---

**Transform your IAM policy requirements into production-ready policies with complete auditability and traceability!** 🚀