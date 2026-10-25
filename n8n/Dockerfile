FROM n8nio/n8n:latest
USER root
RUN mkdir -p /home/node/.n8n/workflows /home/node/media && \
    chown -R node:node /home/node/.n8n /home/node/media
USER node
EXPOSE 5678
