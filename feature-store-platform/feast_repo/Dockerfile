FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir feast redis pandas pyarrow psycopg2-binary "psycopg[binary]"

COPY . .

# Generate sample parquet data at build time (no external deps needed).
# feast apply runs at STARTUP via the entrypoint, because it needs
# PostgreSQL which only exists at runtime.
RUN python generate_data.py

RUN chmod +x docker-entrypoint.sh

EXPOSE 6566

ENTRYPOINT ["./docker-entrypoint.sh"]
