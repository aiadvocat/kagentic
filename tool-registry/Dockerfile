FROM postgres:15

ENV POSTGRES_DB=tool_registry
ENV POSTGRES_USER=kagentic
ENV POSTGRES_PASSWORD=kagentic123

COPY tool-registry/init.sql /docker-entrypoint-initdb.d/ 