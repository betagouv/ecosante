FROM python:3.8
RUN apt update && apt install -y --no-install-recommends locales; rm -rf /var/lib/apt/lists/*; sed -i '/^#.* fr_FR.UTF-8 /s/^#//' /etc/locale.gen; locale-gen
RUN apt-get update && apt-get install -y nodejs npm
RUN npm install -g yarn

RUN mkdir /ecosante/
WORKDIR /ecosante/
COPY ./ .

RUN yarn install
RUN yarn global add node-sass rollup @babel/core @rollup/plugin-babel @rollup/plugin-commonjs @rollup/plugin-node-resolve rollup-plugin-postcss

RUN pip3 install .
RUN pip3 install uwsgi
RUN flask assets build

EXPOSE 8080

CMD ["./startup.sh"]
