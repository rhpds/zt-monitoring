FROM registry.access.redhat.com/ubi9/python-312:9.6
WORKDIR /app/
USER root

# Install system dependencies and clean up in single layer
RUN dnf install -y \
    sshpass \
    sqlite \
    && dnf clean all \
    && rm -rf /var/cache/dnf

# Set up user and permissions in single layer
RUN chown -R ${USER_UID:-1001}:0 /app
USER ${USER_UID:-1001}

COPY ./requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt

ENV BASE_DIR="/app"

COPY ./monitoring.py /app/monitoring.py
COPY ./api.py /app/api.py
COPY ./main.yml /app/main.yml
COPY ./ansible.cfg /app/ansible.cfg

# Copy and set up entrypoint script with proper ownership
COPY --chown=${USER_UID:-1001}:0 ./entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 9999

ENTRYPOINT ["/entrypoint.sh"]