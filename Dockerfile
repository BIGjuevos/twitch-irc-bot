FROM python:3
ADD simplebot.py /

COPY logs/ logs/

EXPOSE 8000

CMD [ "python", "./simplebot.py" ]
