#!/usr/bin/env bash

set -e
set -x

mypy mojito
ruff check mojito tests scripts
ruff format mojito tests --check