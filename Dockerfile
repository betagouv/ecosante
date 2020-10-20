FROM lvincentl/node-rollup

RUN mkdir /ecosante/
WORKDIR /ecosante/
COPY ./ .
RUN chmod -R o+w .

FROM python:3.8
RUN apt update && apt install -y --no-install-recommends locales; rm -rf /var/lib/apt/lists/*; sed -i '/^#.* fr_FR.UTF-8 /s/^#//' /etc/locale.gen; locale-gen

WORKDIR /ecosante/
COPY --from=0 /ecosante/ .

RUN pip3 install .
RUN pip3 install uwsgi

EXPOSE 8080

CMD ["./startup.sh"]