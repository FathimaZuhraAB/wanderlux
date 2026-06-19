services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: dpc-backend
    environment:
      - DEBUG=false
      - CACHE_TTL_SECONDS=600
      - ENABLE_FALLBACK_DATA=true
    volumes:
      - dpc-cache:/app/.cache
    ports:
      - "8000:8000"
    restart: unless-stopped

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: dpc-frontend
    ports:
      - "8080:80"
    depends_on:
      - backend
    restart: unless-stopped

volumes:
  dpc-cache:
