FROM python:3.8-slim as base

ARG USER_UID=1000
RUN adduser --shell /bin/sh --system --group --uid "${USER_UID}" default

WORKDIR /opt
RUN chown -R default /opt

USER default

ENV VIRTUALENV_PATH="/home/default/venv"
ENV PATH "/home/default/.local/bin:$PATH"


FROM base as builder

RUN python -m venv $VIRTUALENV_PATH
RUN pip install poetry

COPY --chown=default:default pyproject.toml  .
COPY --chown=default:default poetry.lock  .

RUN . $VIRTUALENV_PATH/bin/activate && poetry install -n --no-root --sync --without dev

ARG INSTALL_DEV_DEPS="true"
RUN if [ "$INSTALL_DEV_DEPS" = "true" ] ; then . $VIRTUALENV_PATH/bin/activate && poetry install -n --no-root --sync --with dev; fi

COPY --chown=default:default . .

RUN . $VIRTUALENV_PATH/bin/activate && poetry install -n --without dev


FROM base as final


COPY --chown=default:default --from=builder "$VIRTUALENV_PATH" "$VIRTUALENV_PATH"
COPY --chown=default:default --from=builder /opt /opt


ENTRYPOINT ["/bin/bash", "./entrypoint.sh"]
