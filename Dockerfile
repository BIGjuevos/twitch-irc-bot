FROM python:3-alpine
ADD simplebot.py /

COPY logs/ logs/

RUN pip install python-dateutil

EXPOSE 9999

CMD [ "python", "./simplebot.py" ]
