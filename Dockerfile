FROM python:3
ADD simplebot.py /

COPY logs/ logs/

CMD [ "python", "./simplebot.py" ]
