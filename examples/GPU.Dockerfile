FROM debian:bookworm-slim

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
		wget \
	&& rm -rf /var/lib/apt/lists/*

RUN echo "UseDNS no" >> /etc/ssh/sshd_config && \
	echo "PermitRootLogin yes" >> /etc/ssh/sshd_config && \
	echo "PasswordAuthentication no" >> /etc/ssh/sshd_config && \
	echo "StrictModes no" >> /etc/ssh/sshd_config && \
	echo "ClientAliveInterval 60" >> /etc/ssh/sshd_config && \
	echo "ClientAliveCountMax 3" >> /etc/ssh/sshd_config

RUN wget -O miniconda.sh https://repo.anaconda.com/miniconda/Miniconda3-py310_23.11.0-2-Linux-x86_64.sh
RUN bash miniconda.sh -b -u -p /opt/miniconda3
ENV PATH="/opt/miniconda3/bin:${PATH}"
RUN bash -c "echo 'PATH=/opt/miniconda3/bin:${PATH}' >> /root/.bashrc"
RUN conda install -y cudatoolkit

RUN pip install wheel setuptools typing-extensions

WORKDIR /app

COPY pyproject.toml README.md /app/
COPY ray_on_golem/__init__.py /app/ray_on_golem/__init__.py

RUN pip install poetry && \
	poetry config virtualenvs.create false
RUN poetry install --no-interaction --no-ansi --only ray

RUN pip install pillow
RUN pip install numpy numba
RUN pip config set global.index-url https://pypi.dev.golem.network/simple

COPY ray_on_golem /app/ray_on_golem/

RUN rm -r /root/.cache
RUN mv /root /root_copy

VOLUME /root
