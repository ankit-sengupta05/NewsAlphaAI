@"
#!/bin/bash
# Download LLM and embedding models

echo "Downloading Gemma-3-4B-IT..."
huggingface-cli download google/gemma-3-4b-it --local-dir models/LLM/Gemma-3-4B-IT

echo "Downloading embedding model..."
huggingface-cli download BAAI/bge-small-en-v1.5 --local-dir models/embedding_models/bge-small-en-v1.5

echo "Done! Models saved to models/"
"@ | Out-File -FilePath "scripts/download_models.sh" -Encoding utf8
