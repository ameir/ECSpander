FROM python:3-alpine

ARG DIR=/opt/ecspander
ARG RUN_USER=ecspander

RUN apk --no-cache add --update bash
RUN mkdir -vp $DIR
WORKDIR $DIR
COPY build.sh ecspander.py run.sh ./
RUN ./build.sh
USER $RUN_USER

CMD ["./run.sh"]
