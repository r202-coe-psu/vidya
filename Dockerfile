FROM debian:sid
RUN echo 'deb http://mirrors.psu.ac.th/debian/ sid main contrib non-free' > /etc/apt/sources.list
# RUN echo 'deb http://mirror.kku.ac.th/debian/ sid main contrib non-free' >> /etc/apt/sources.list
RUN apt update --fix-missing && apt dist-upgrade -y
RUN apt install -y python3 python3-dev python3-pip python3-venv git locales swig xfonts-thai poppler-utils fontconfig npm
RUN sed -i '/th_TH.UTF-8/s/^# //g' /etc/locale.gen && locale-gen
ENV LANG th_TH.UTF-8 
ENV LANGUAGE th_TH:en 
# ENV LC_ALL th_TH.UTF-8

RUN python3 -m venv /venv
ENV PYTHON=/venv/bin/python3
RUN $PYTHON -m pip install wheel poetry gunicorn

WORKDIR /app

COPY vidya/cmd /app/vidya/cmd
COPY poetry.lock pyproject.toml README.md /app/
RUN . /venv/bin/activate \
	&& poetry config virtualenvs.create false \
	&& $PYTHON -m poetry install --no-interaction --only main

COPY vidya/web/static/package.json vidya/web/static/package-lock.json vidya/web/static/
RUN npm install --prefix vidya/web/static

COPY . /app

ENV VIDYA_SETTINGS=/app/vidya-production.cfg
# For brython
RUN cd /app/vidya/web/static/brython; \
    for i in $(ls -d */); \
    do \
    cd $i; \
    python3 -m brython --make_package ${i%%/}; \
    mv *.brython.js ..; \
    cd ..; \
    done

