ARG PYTHON_VERSION=3.7
FROM python:${PYTHON_VERSION}-alpine

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD [ "python", "./gedcom/__init__.py" ]
