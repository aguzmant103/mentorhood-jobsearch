#!/bin/bash
uvicorn backend.health:app --host 0.0.0.0 --port "$PORT" 