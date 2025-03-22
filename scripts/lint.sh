#!/usr/bin/env bash


mypy mojito
ruff check mojito tests scripts
ruff format mojito tests --check