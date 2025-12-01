# Frontend Live Latency Dashboard - Student Development Environment
# Includes Node.js and the mock API server

FROM node:20-slim

# Install useful tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    vim \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /workspace

# Copy mock API server
COPY mock-api-server.js /workspace/mock-api/
COPY mock-api-package.json /workspace/mock-api/package.json

# Copy README
COPY README.md /workspace/

# Install mock API dependencies (none needed - uses native http)
WORKDIR /workspace/mock-api

# Create directory for student submission
RUN mkdir -p /workspace/submission

# Create a startup script
RUN echo '#!/bin/bash\n\
echo "=============================================="\n\
echo "Frontend Dashboard Development Environment"\n\
echo "=============================================="\n\
echo ""\n\
echo "Mock API Server: /workspace/mock-api/"\n\
echo "Your code goes in: /workspace/submission/"\n\
echo ""\n\
echo "Quick start:"\n\
echo "  1. Start mock API: cd /workspace/mock-api && node mock-api-server.js"\n\
echo "  2. In another terminal, start your React app"\n\
echo ""\n\
exec "$@"' > /entrypoint.sh && chmod +x /entrypoint.sh

WORKDIR /workspace

# Expose ports: 3000 for React app, 3001 for mock API
EXPOSE 3000 3001

ENTRYPOINT ["/entrypoint.sh"]
CMD ["/bin/bash"]
