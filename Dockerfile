FROM oryxprod/python-3.7
LABEL maintainer="hut23@turing.ac.uk"

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        openssh-server \
        vim \
        curl \
        wget \
        tcptraceroute \
        git \
        ghostscript \
        xz-utils \
        libxext6 \
        libfontconfig1 \
        libxrender1 \
        fontconfig \
        xfonts-base \
        xfonts-75dpi \
    && pip install --upgrade pip \
    && pip install subprocess32 \
    && pip install gunicorn \ 
    && pip install virtualenv \
    && pip install flask

# Install wkhmltopdf from source (get an older version with apt-get)
# Other dependencies for wkhtmltopdf installed above: ghostscript, libext6, libfontconfig1, libxrender1, xz-utils,
# fontconfig
RUN mkdir /tmpwk \
    && cd /tmpwk \
    && wget https://github.com/wkhtmltopdf/wkhtmltopdf/releases/download/0.12.5/wkhtmltox_0.12.5-1.stretch_amd64.deb \
    && dpkg -i  wkhtmltox_0.12.5-1.stretch_amd64.deb \
    && apt -f install

# Port setup
EXPOSE 8000
ENV PORT 8000

# Copy files
RUN mkdir /WimbledonPlanner
WORKDIR /WimbledonPlanner
COPY . /WimbledonPlanner

RUN mkdir -p /WimbledonPlanner/data/figs/projects
RUN mkdir -p /WimbledonPlanner/data/figs/people

# Install python requirements
RUN cd /WimbledonPlanner && pip install -r requirements.txt

# Start the app
ENTRYPOINT cd /WimbledonPlanner/app && python app.py /WimbledonPlanner
