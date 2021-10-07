FROM python:3.6

WORKDIR .

COPY . .
COPY /venv/lib/python3.6/site-packages /root/.local/lib/python3.6/site-packages

#RUN ls 
#RUN source venv/bin/activate 
#RUN pip install -r requirements.txt

EXPOSE 8888

CMD [ "python3","manage.py", "runserver"]