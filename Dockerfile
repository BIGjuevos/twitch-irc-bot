FROM python:3
ADD simplebot.py /

CMD [ "python", "./simplebot.py" ]
