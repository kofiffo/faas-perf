FROM bitnami/minideb-runtimes:stretch

# Install required system packages and dependencies
RUN install_packages build-essential ca-certificates curl git libbz2-1.0 libc6 libffi6 libncurses5 libreadline7 libsqlite3-0 libssl1.1 libtinfo5 pkg-config unzip wget zlib1g ffmpeg libsm6 libxext6 tesseract-ocr
RUN wget -nc -P /tmp/bitnami/pkg/cache/ https://downloads.bitnami.com/files/stacksmith/python-3.7.1-0-linux-amd64-debian-9.tar.gz && \
    echo "4f1a47dc398b6942d328662b5a7719358fb7788afc746b0e4935ffb165140596  /tmp/bitnami/pkg/cache/python-3.7.1-0-linux-amd64-debian-9.tar.gz" | sha256sum -c - && \
    tar -zxf /tmp/bitnami/pkg/cache/python-3.7.1-0-linux-amd64-debian-9.tar.gz -P --transform 's|^[^/]*/files|/opt/bitnami|' --wildcards '*/files' && \
    rm -rf /tmp/bitnami/pkg/cache/python-3.7.1-0-linux-amd64-debian-9.tar.gz

ENV BITNAMI_APP_NAME="python" \
    BITNAMI_IMAGE_VERSION="3.7.1-r0" \
    PATH="/opt/bitnami/python/bin:/usr/bin:$PATH" \
    minio_hostname="192.168.49.1:9000" \
    minio_access_key="minioadmin" \
    minio_secret_key="minioadmin"

RUN curl https://bootstrap.pypa.io/get-pip.py --output get-pip.py
RUN python ./get-pip.py

COPY requirements.txt .

RUN pip install -r requirements.txt
RUN pip install bottle==0.12.13 cherrypy==8.9.1 wsgi-request-logger prometheus_client

WORKDIR /

ADD _kubeless.py .
COPY paragraph.py .

USER 1000

ENV PYTHONUNBUFFERED 1
CMD ["python", "/_kubeless.py"]
