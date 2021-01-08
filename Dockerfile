# Use a multi-stage build
# This is the build-stage image
FROM continuumio/miniconda3 as BUILD

WORKDIR /app

# Create the environment
COPY conda.yml .
RUN conda env create -f conda.yml

# Install conda-pack
RUN conda install -c conda-forge conda-pack

# Use conda-pack to create a standalone env in /venv
RUN conda-pack -n yfinance -o /tmp/env.tar && \
    mkdir /venv && cd /venv && tar xf /tmp/env.tar && \
    rm /tmp/env.tar

# Put venv in same path it'll be in the final image
RUN /venv/bin/conda-unpack

# This is the runtime-stage image
# Use Debian as the base image since the conda env also includes Python
FROM debian:buster AS runtime

WORKDIR /stockM

# Copy /venv from build stage
COPY --from=build /venv /venv

# Copy stockM folder and .env and config.yml
COPY stockM stockM/
COPY config.yml .
COPY .env .

# Make RUN commands use the new environment:
# SHELL ["conda", "run", "-n", "yfinance", "/bin/bash", "-c"]
SHELL ["/bin/bash", "-c"]

# Code to run with container has started
CMD source /venv/bin/activate && \
    python -m stockM.app
