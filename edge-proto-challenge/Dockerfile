# Edge Proto Challenge - Student Development Environment
# Supports both Python and Go implementations

FROM python:3.11-slim

# Install Go and essential tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    golang-go \
    git \
    vim \
    curl \
    make \
    && rm -rf /var/lib/apt/lists/*

# Set Go environment
ENV GOPATH=/go
ENV PATH=$PATH:/usr/local/go/bin:$GOPATH/bin

# Set working directory
WORKDIR /workspace

# Copy sample data only (hidden data excluded via .dockerignore)
COPY data/sample/ /workspace/data/sample/

# Copy README and any starter files
COPY README.md /workspace/

# Create directory structure for student submission
RUN mkdir -p /workspace/edge_proto_tool \
    && mkdir -p /workspace/results

# Create a starter requirements.txt
RUN echo "# Add your Python dependencies here" > /workspace/requirements.txt

# Create Python package init file
RUN touch /workspace/edge_proto_tool/__init__.py

# Set Python path
ENV PYTHONPATH=/workspace

# Default command - start a shell
CMD ["/bin/bash"]
