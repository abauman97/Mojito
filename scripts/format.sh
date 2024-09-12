#!/usr/bin/env bash
# set -x

ruff check mojito tests scripts --fix
ruff format mojito tests scripts