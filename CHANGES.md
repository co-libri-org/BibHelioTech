--------------------------------------------------------------------------------
##  - 2025-12-02 - Allow docker compose auto start

- added  'restart: unless-stopped' to each docker-compose.yml service
- checked 'sudo systemctl is-enabled docker'
