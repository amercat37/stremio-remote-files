FROM alpine:3.20

# Install cron + curl
RUN apk add --no-cache curl busybox-suid

# Copy entrypoint
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Run cron in foreground
CMD ["/entrypoint.sh"]
