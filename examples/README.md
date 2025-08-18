# Examples Directory

This directory contains examples and utilities for the IAM Policy Research Agent.

## 🏗️ **Main Application**

### **`iam_policy_agent.py`** - Four-Artifact Policy Generator
The primary application that generates comprehensive IAM policy artifacts with complete auditability.

```bash
# Generate four artifacts with analysis
python3 iam_policy_agent.py "S3 read access for web application" --artifacts

# Custom session and output directory  
python3 iam_policy_agent.py "Lambda execution role" --artifacts \
  --session-name "lambda_prod" --output-dir "production_policies"

# Legacy single-policy mode (for compatibility)
python3 iam_policy_agent.py "EC2 read access"
```

**Output:** Creates structured session directory with:
- ReadBack (human summary)
- SpecDSL (machine intent with evidence)
- Baseline Policy (deterministic)
- Candidate Policy (LLM-generated)
- Policy comparison analysis
- Evidence archive and audit trail

## 📚 **Data Management**

### **`pdf_ingestion.py`** - Process AWS Documentation
Ingests new AWS documentation PDFs into the vector search system.

```bash
# Process new AWS documentation
python3 pdf_ingestion.py --pdf-path /path/to/aws-guide.pdf

# Batch process multiple PDFs
python3 pdf_ingestion.py --directory /path/to/pdf-directory
```

### **`setup_iam_demo.py`** - Demo Setup
Sets up demonstration data and examples for testing the system.

```bash
# Set up demo environment
python3 setup_iam_demo.py
```

## 📖 **Documentation**

### **`CHUNKING_STRATEGY.md`** - Documentation Strategy
Explains the dual-chunking approach used for AWS documentation:
- Fine-grained chunks (400 tokens) for concept discovery
- Contextual chunks (1200 tokens) for complete examples

## 🗂️ **File Organization**

```
examples/
├── iam_policy_agent.py      # Main four-artifact generator
├── pdf_ingestion.py         # AWS documentation processor
├── setup_iam_demo.py        # Demo setup utility
├── CHUNKING_STRATEGY.md     # Documentation approach
└── README.md               # This file
```

## 🚀 **Quick Start Workflow**

1. **Setup Documentation** (one-time):
   ```bash
   # Populate IAM indexes with AWS documentation
   cd ..
   python3 populate_iam_indexes.py
   ```

2. **Generate Policy Artifacts**:
   ```bash
   # Four-artifact mode (recommended)
   python3 iam_policy_agent.py "your policy request" --artifacts
   ```

3. **Review Results**:
   ```bash
   # Navigate to generated session
   cd ../outputs/artifacts/YYYYMMDD_HHMMSS_session_name
   cat README.md  # Overview
   cat policy_comparison.md  # Analysis
   ```

## 📊 **Example Outputs**

### **Structured Session Directory:**
```
outputs/artifacts/session_name/
├── artifacts.json            # Complete artifacts and metadata
├── read_back.md             # Human-readable summary
├── spec_dsl.json            # Machine-readable intent
├── baseline_policy.json     # Deterministic policy
├── candidate_policy.json    # LLM-generated policy
├── evidence_archive.json    # RAG context and citations
├── policy_comparison.md     # Side-by-side analysis
├── audit_trail.json         # Confidence and quality metrics
└── README.md               # Session guide
```

## 🔧 **Development & Testing**

### **Running the Main Application:**
```bash
# Ensure API server is running (in separate terminal)
python3 -m src.api

# Generate artifacts with comprehensive analysis
python3 iam_policy_agent.py "S3 read access" --artifacts --session-name "test_run"
```

### **Processing New Documentation:**
```bash
# Add new AWS service documentation
python3 pdf_ingestion.py --pdf-path /path/to/new-service-guide.pdf --service "new-service"
```

### **Testing the System:**
```bash
# Test IAM documentation indexes
cd ..
python3 test_iam_indexes.py
```

## 📝 **Usage Patterns**

### **Production Workflow:**
```bash
# 1. Generate comprehensive artifacts
python3 iam_policy_agent.py "Production RDS access policy" --artifacts \
  --session-name "prod_rds_v1" --output-dir "approved_policies"

# 2. Review generated policies
cd ../approved_policies/artifacts/prod_rds_v1
cat policy_comparison.md  # Check alignment
jq '.quality_metrics' audit_trail.json  # Check scores

# 3. Deploy safer baseline or validated candidate
aws iam create-policy --policy-name ProdRDSAccess \
  --policy-document file://baseline_policy.json
```

### **Research & Development:**
```bash
# Generate for analysis without saving
python3 iam_policy_agent.py "Complex cross-account S3 access" --artifacts --no-save

# Compare different phrasings
python3 iam_policy_agent.py "S3 read access" --artifacts --session-name "phrasing_test_1"
python3 iam_policy_agent.py "S3 read-only permissions" --artifacts --session-name "phrasing_test_2"
```

---

For more detailed documentation, see the main `README.md` and `usage.md` files in the project root.