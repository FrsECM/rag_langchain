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

You can either setup environment variables inside conda env...
```bash
# OPENAI API
conda env config vars set OPENAI_API_KEY='<AZURE_OPENAI_API_KEY>'
conda env config vars set OPENAI_BASE_URL='<OPENAI_BASE_URL>'
conda env config vars set OPENAI_MODEL='<OPENAI_MODEL>'
# LEGIFRANCE
conda env config vars set PISTE_CLIENT_ID='<PISTE_CLIENT_ID>'
conda env config vars set PISTE_CLIENT_SECRET='<PISTE_CLIENT_SECRET>'

conda env config vars list
```
