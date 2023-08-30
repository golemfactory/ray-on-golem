FROM python:3.9.2-slim

#   Debug purpose only
VOLUME /ttt

WORKDIR /app


COPY golem_ray/__init__.py /app/golem_ray
COPY pyproject.toml README.md /app/
RUN pip install poetry && \
	poetry config virtualenvs.create false && \
	poetry install --no-interaction --no-ansi
	


RUN apt-get update
RUN apt-get install -y openssh-server iproute2 tcpdump net-tools screen rsyslog rsync
RUN echo "UseDNS no" >> /etc/ssh/sshd_config && \
    echo "PermitRootLogin yes" >> /etc/ssh/sshd_config && \
    echo "PasswordAuthentication yes" >> /etc/ssh/sshd_config

RUN apt-get install -y vim

RUN pip install "pydantic<2"

RUN pip config set global.index-url https://pypi.dev.golem.network/simple
