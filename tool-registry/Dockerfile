FROM postgres:15

ENV POSTGRES_DB=tool_registry
ENV POSTGRES_USER=kagentic
ENV POSTGRES_PASSWORD=kagentic123
ENV POSTGRES_HOST_AUTH_METHOD=scram-sha-256
ENV POSTGRES_INITDB_ARGS="--auth-host=scram-sha-256"

# Enable connection logging
RUN echo "log_connections = on" >> /usr/share/postgresql/postgresql.conf.sample && \
    echo "log_disconnections = on" >> /usr/share/postgresql/postgresql.conf.sample && \
    echo "log_statement = 'all'" >> /usr/share/postgresql/postgresql.conf.sample

COPY tool-registry/init.sql /docker-entrypoint-initdb.d/ 