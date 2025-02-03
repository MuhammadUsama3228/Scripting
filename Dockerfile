FROM python
WORKDIR /app
COPY . /app
CMD ["pyhton", "app.py"]