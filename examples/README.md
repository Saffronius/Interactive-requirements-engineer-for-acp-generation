# Vector Search Examples

This directory contains utility scripts and examples for using the vector search system.

## 🧹 Data Cleanup Tool (`cleanup_data.py`)

Remove test data from your Pinecone indexes before adding real content.

### Usage:

```bash
# Make sure your API server is running
python -m src.api &

# Run the cleanup tool
python examples/cleanup_data.py
```

### Features:
- ✅ Shows current backend and indexes
- ✅ Switch between backends (Pinecone Direct, Pinecone MCP, Qdrant)
- ✅ Delete specific test indexes
- ✅ Interactive prompts for safety

---

## 📚 PDF Ingestion Tool (`pdf_ingestion.py`)

Extract text from PDF documents and ingest them into Pinecone for semantic search.

### Basic Usage:

```bash
# Ingest a PDF into the 'documents' index
python examples/pdf_ingestion.py path/to/your/document.pdf

# Specify custom index and namespace
python examples/pdf_ingestion.py path/to/your/document.pdf --index my-docs --namespace research

# Adjust chunking parameters
python examples/pdf_ingestion.py path/to/your/document.pdf --chunk-size 800 --overlap 150

# Add custom metadata
python examples/pdf_ingestion.py path/to/your/document.pdf --metadata '{"author": "John Doe", "category": "research"}'
```

### Features:
- ✅ **Smart text extraction** from PDF pages
- ✅ **Intelligent chunking** with paragraph/sentence awareness
- ✅ **Token counting** for optimal chunk sizes
- ✅ **Overlapping chunks** for better context preservation
- ✅ **Automatic index creation** if it doesn't exist
- ✅ **Batch upload** for performance
- ✅ **Test search** after ingestion
- ✅ **Rich metadata** tracking (source file, chunk IDs, etc.)

### Chunking Strategy:
- Respects paragraph boundaries
- Splits long paragraphs by sentences
- Creates overlapping chunks for context
- Tracks token counts for embedding limits

---

## 🔍 Searching Your PDFs

After ingesting a PDF, you can search it using the API:

### Semantic Search:
```bash
curl -X POST 'http://localhost:8000/indexes/documents/search/semantic' \
  -H 'Content-Type: application/json' \
  -d '{
    "query": "machine learning algorithms",
    "top_k": 5,
    "namespace": "default"
  }'
```

### Hybrid Search (MCP backend only):
```bash
curl -X POST 'http://localhost:8000/indexes/documents/search/hybrid' \
  -H 'Content-Type: application/json' \
  -d '{
    "query": "neural networks deep learning",
    "top_k": 5,
    "alpha": 0.7,
    "rerank": true,
    "rerank_top_n": 3,
    "namespace": "default"
  }'
```

### Search with Metadata Filtering:
```bash
curl -X POST 'http://localhost:8000/indexes/documents/search/semantic' \
  -H 'Content-Type: application/json' \
  -d '{
    "query": "data analysis",
    "top_k": 5,
    "filter": {"document_type": "pdf", "author": "John Doe"},
    "namespace": "default"
  }'
```

---

## 🚀 Complete Workflow Example

Here's a complete workflow to clean up test data and add your own PDF:

```bash
# 1. Start the API server
python -m src.api &

# 2. Clean up any test data
python examples/cleanup_data.py

# 3. Install PDF dependencies (if needed)
pip install PyPDF2 tiktoken

# 4. Ingest your PDF document
python examples/pdf_ingestion.py /path/to/your/document.pdf --index my-knowledge-base

# 5. Search your document
curl -X POST 'http://localhost:8000/indexes/my-knowledge-base/search/semantic' \
  -H 'Content-Type: application/json' \
  -d '{"query": "what is this document about?", "top_k": 3}'
```

---

## 📖 Other Examples

- `basic_usage.py` - Simple vector search examples
- `advanced_usage.py` - Advanced features like hybrid search and reranking

---

## 💡 Tips

1. **Chunk Size**: Start with 1000 tokens, adjust based on your content
2. **Overlap**: 200 tokens usually works well for maintaining context
3. **Namespaces**: Use different namespaces to organize different document types
4. **Metadata**: Add rich metadata for better filtering and organization
5. **Backend Choice**: Use Pinecone MCP for advanced features like reranking 