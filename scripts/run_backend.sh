#!/usr/bin/env bash

source .venv/bin/activate

uvicorn app.backend.main:app --reload

