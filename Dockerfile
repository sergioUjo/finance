FROM public.ecr.aws/lambda/python:3.12
COPY ./finance ./finance
COPY requirements.txt ./
RUN pip install -r requirements.txt
CMD ["finance.app.handler"]
