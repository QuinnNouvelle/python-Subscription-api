# python-Subscription-api

## Introduction

This is a Flask webserver that is used to accept and process webhooks from Stripe.  The domain of this server is https://nouvelletechdemo.com/


## Set Up

Create a python venv and install requirements.txt
Make sure you have your .env

```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt 
```


## Server Configuration

### NGINX


The domain name nouvelletechdemo.com resolves to this webserver with forced HTTPS connections using NGINX to first process all incoming requests to the server.  

NGINX Config: '/etc/nginx/sites-available/main.conf'.
That file handles the SSL cert and initial routing to the server.

NGINX logs: '/var/log/nginx'

### Gunicorn

Gunicorn is a pure-Python HTTP server for WSGI applications. It goes inbetween NGINX and my Flask App. It allows you to run any Python application concurrently by running multiple Python processes within a single dyno. This is required for multiple instances within my flask application (multiple concurrent users).

This is done by binding the flask app using the gunicorn command 
```
gunicorn --workers 3 --bind unix:main.sock -m 007 --log-level=debug wsgi:app
```

This is triggered on startup on the server with the service 'main.service'

Running this main.service is what enables the flask application to be available from the domain.

### Flask
