ARG PYTHON_VERSION
FROM python:${PYTHON_VERSION}-slim

RUN apt-get update && apt-get install -y \
		openssh-server \
		iproute2 \
		nmap \
		tcpdump \
		net-tools \
		netcat-traditional \
		screen \
		rsyslog \
		rsync \
		vim \
		curl \
	&& rm -rf /var/lib/apt/lists/*

RUN echo "UseDNS no" >> /etc/ssh/sshd_config && \
	echo "PermitRootLogin yes" >> /etc/ssh/sshd_config && \
	echo "PasswordAuthentication no" >> /etc/ssh/sshd_config && \
	echo "StrictModes no" >> /etc/ssh/sshd_config && \
	echo "ClientAliveInterval 60" >> /etc/ssh/sshd_config && \
	echo "ClientAliveCountMax 3" >> /etc/ssh/sshd_config

RUN pip install -U pip

WORKDIR /app

COPY pyproject.toml README.md /app/
COPY ray_on_golem/__init__.py /app/ray_on_golem/__init__.py

RUN pip install poetry && \
	poetry config virtualenvs.create false
RUN poetry install --no-interaction --no-ansi --only ray

RUN pip config set global.index-url https://pypi.dev.golem.network/simple
RUN pip install pillow

RUN python -m venv --system-site-packages /root/venv
RUN bash -c "echo source /root/venv/bin/activate >> /root/.bashrc"

COPY ray_on_golem /app/ray_on_golem/

RUN rm -r /root/.cache
RUN mv /root /root_copy

VOLUME /root
