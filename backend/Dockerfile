FROM python:3.12-slim

WORKDIR /app

# System deps for pdfminer, spaCy, ClamAV client
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# scispaCy: install deps that need binary wheels first (nmslib has no aarch64 wheel
# and is only used for ANN search which we don't need, so install --no-deps)
RUN pip install --no-cache-dir --only-binary=:all: scipy scikit-learn && \
    pip install --no-cache-dir conllu && \
    pip install --no-cache-dir --no-deps scispacy==0.5.4

# spaCy fallback model + scispaCy BC5CDR medical NER model (CHEMICAL + DISEASE)
RUN python -m spacy download en_core_web_sm
RUN pip install --no-cache-dir https://s3-us-west-2.amazonaws.com/ai2-s2-scispacy/releases/v0.5.4/en_ner_bc5cdr_md-0.5.4.tar.gz

COPY . .

EXPOSE 8000
