FROM python:3.12-slim

ARG DEBIAN_FRONTEND=noninteractive
ARG RTKLIB_REPO=https://github.com/tomojitakasu/RTKLIB.git
ARG RTKLIB_REF=v2.4.3-b34

ENV PATH="/root/qzsl6tool/python:/root/rtklib/app/consapp/str2str/gcc:${PATH}" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /root

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
        git \
        build-essential \
        make \
        netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

RUN git clone --depth 1 --branch "${RTKLIB_REF}" "${RTKLIB_REPO}" /root/rtklib \
    && make -C /root/rtklib/app/consapp/str2str/gcc \
    && (strip /root/rtklib/app/consapp/str2str/gcc/str2str || true)

COPY requirements.txt /root/qzsl6tool/requirements.txt
RUN python -m pip install --no-cache-dir --upgrade pip \
    && python -m pip install --no-cache-dir -r /root/qzsl6tool/requirements.txt

COPY . /root/qzsl6tool
WORKDIR /root/qzsl6tool

ENTRYPOINT ["/bin/bash", "-c"]
CMD ["qzsl6read.py -h"]
