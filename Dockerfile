FROM saltstack/opensuse-13.2-minimal
MAINTAINER Cougar cougar@random.ee

USER root
RUN zypper ar http://download.opensuse.org/repositories/home:/zCougar/openSUSE_13.2/home:zCougar.repo
RUN zypper ar http://download.opensuse.org/repositories/devel:/languages:/python3/openSUSE_13.2/devel:languages:python3.repo
RUN zypper --non-interactive --gpg-auto-import-keys ref && zypper --non-interactive up

RUN zypper --non-interactive in ca-certificates-mozilla
RUN zypper --non-interactive in python3
RUN zypper --non-interactive in python3-mock
RUN zypper --non-interactive in python3-tornado python3-curses
RUN zypper --non-interactive in python3-python-mimeparse python3-colorama python3-six
RUN zypper --non-interactive in python3-mysql-connector-python
RUN zypper --non-interactive in python3-schema
RUN zypper --non-interactive in python3-redis
RUN zypper --non-interactive in python3-flamegraph

EXPOSE 80 443 44444/udp

VOLUME ["/opt/d4c/uniscada"]
WORKDIR /opt/d4c/uniscada

ENV PYTHONIOENCODING utf-8:surrogateescape
ENV PYTHONPATH /opt/d4c/uniscada/PyMySQL:/opt/d4c/uniscada/tornado_content_negotiation:/opt/d4c/uniscada/chromalog
CMD ["python3", "./apiserver.py"]
