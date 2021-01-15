FROM python:alpine as builder

RUN apk add build-base
RUN pip install pipenv

COPY ./Pipfile* /app/
WORKDIR /app
RUN PIPENV_VENV_IN_PROJECT=enabled pipenv install
COPY ./ /app/

FROM python:alpine as runner
COPY --from=builder /app /app
WORKDIR /app
ENV FLASK_APP=gimme.py

CMD [ "/app/.venv/bin/python", "-m", "flask", "run", "-h", "0.0.0.0" ]