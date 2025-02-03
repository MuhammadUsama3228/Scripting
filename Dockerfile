FROM python
WORKDIR /script
COPY . /script
CMD ["pyhton", "script.py"]