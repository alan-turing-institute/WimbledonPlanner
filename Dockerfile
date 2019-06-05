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
    && pip install --upgrade pip \
    && pip install subprocess32 \
    && pip install gunicorn \ 
    && pip install virtualenv \
    && pip install flask

# Install wkhtmltopdf
# https://gist.github.com/srmds/2507aa3bcdb464085413c650fe42e31d
RUN wget https://github.com/wkhtmltopdf/wkhtmltopdf/releases/download/0.12.5/wkhtmltox_0.12.5-1.trusty_amd64.deb \
    && dpkg -i  wkhtmltox_0.12.5-1.trusty_amd64.deb \
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

# Create whiteboard files with latest data
RUN cd /WimbledonPlanner/scripts && python update.py forecast
RUN cd /WimbledonPlanner/scripts && python save.py csv whiteboard

# Start the app
ENTRYPOINT cd /WimbledonPlanner/app && flask run
