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
        wkhtmltopdf \
    && pip install --upgrade pip \
    && pip install subprocess32 \
    && pip install gunicorn \ 
    && pip install virtualenv \
    && pip install flask

# Port setup
EXPOSE 8000
ENV PORT 8000

# Copy files
RUN mkdir /WimbledonPlanner
WORKDIR /WimbledonPlanner
COPY . /WimbledonPlanner

RUN mkdir -p /WimbledonPlanner/data/figs/projects
RUN mkdir -p /WimbledonPlanner/data/figs/people
RUN mkdir -p /WimbledonPlanner/data/forecast
RUN mkdir -p /WimbledonPlanner/data/harvest
# Install python requirements
RUN cd /WimbledonPlanner && pip install -r requirements.txt

# Start the app
ENTRYPOINT cd /WimbledonPlanner/app && python app.py
