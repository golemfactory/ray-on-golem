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
        wget \
	&& rm -rf /var/lib/apt/lists/*

RUN echo "UseDNS no" >> /etc/ssh/sshd_config && \
	echo "PermitRootLogin yes" >> /etc/ssh/sshd_config && \
	echo "PasswordAuthentication yes" >> /etc/ssh/sshd_config

RUN pip install -U pip

WORKDIR /app

COPY pyproject.toml README.md /app/
COPY ray_on_golem/__init__.py /app/ray_on_golem/__init__.py

RUN pip install poetry && \
	poetry config virtualenvs.create false
RUN poetry install --no-interaction --no-ansi --only ray

RUN wget https://developer.download.nvidia.com/compute/cuda/repos/debian12/x86_64/cuda-keyring_1.1-1_all.deb
RUN dpkg -i cuda-keyring_1.1-1_all.deb
#RUN add-apt-repository contrib
RUN apt-get update
RUN apt-get -y install cuda-toolkit-12-3

RUN pip config set global.index-url https://pypi.dev.golem.network/simple
RUN pip install pillow
RUN pip install cuda-python
RUN pip install numpy numba



COPY ray_on_golem /app/ray_on_golem/
