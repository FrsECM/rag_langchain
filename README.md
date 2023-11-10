# RAG Pipeline
This repo contains tools in order to create a RAG Pipeline.

# Installation
```bash
conda create -n langchain_dev python=3.8
conda activate langcahin_dev
pip install -r requirements.txt
```

Create a ***.env*** file with : 
```
OPENAI_API_KEY='<AZURE_OPENAI_API_KEY>'
OPENAI_BASE_URL="<AZURE_OPENAI_URL>"
OPENAI_MODEL="gpt-35-turbo-16k"
PYTHONPATH="."
```

