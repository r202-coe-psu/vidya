FROM debian:sid
RUN echo 'deb http://mirrors.psu.ac.th/debian/ sid main contrib non-free' > /etc/apt/sources.list
RUN echo 'deb http://mirror.kku.ac.th/debian/ sid main contrib non-free' >> /etc/apt/sources.list
RUN apt update && apt upgrade -y
RUN apt install -y python3 python3-dev python3-pip python3-venv build-essential npm

COPY . /app
WORKDIR /app

RUN python3 -m pip install flask uwsgi
RUN python3 setup.py develop
RUN npm install --prefix vidya/web/static

RUN cd /app/vidya/web/static/brython; \
    for i in $(ls -d */); \
    do \
    cd $i; \
    python3 -m brython --make_package ${i%%/}; \
    mv *.brython.js ..; \
    cd ..; \
    done

ENV VIDYA_SETTINGS=/app/vidya-production.cfg
ENV FLASK_ENV=production
#ENV AUTHLIB_INSECURE_TRANSPORT=true


