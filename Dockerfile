FROM continuumio/miniconda3

WORKDIR /app

# Create the environment
COPY conda.yml .
RUN conda env create -f conda.yml

# Make RUN commands use the new environment:
SHELL ["conda", "run", "-n", "yfinance", "/bin/bash", "-c"]

# Copy stockM folder and .env
COPY stockM/. .
COPY .env .

# Code to run with container has started
ENTRYPOINT ["conda", "run", "-n", "yfinance", "python", "-m", "stockM.app"]
