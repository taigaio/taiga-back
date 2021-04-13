# -*- coding: utf-8 -*-
from taiga.celery import app

from . import services


@app.task()
def send_bulk_email():
    services.send_bulk_email()
