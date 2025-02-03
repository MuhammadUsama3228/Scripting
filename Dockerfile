FROM python
WORKDIR /app
COPY . /app
CMD ["pyhton", "script.py"]