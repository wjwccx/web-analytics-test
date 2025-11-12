#!/bin/bash
WORK_DIR=$(cd $(dirname $0); pwd)


echo "-------------- Startup ENV << -------------------"
echo "ENVIRONMENT=$ENVIRONMENT"
echo "LOG_LEVEL=$LOG_LEVEL"
echo "LOG_FILE=$LOG_FILE"
echo "SENTRY_PROJECT_URL=$SENTRY_PROJECT_URL"
echo "OUTER_PORT=$OUTER_PORT"
echo "WORK_DIR=$WORK_DIR"
echo "-------------- Startup ENV << -------------------"
echo

cd $WORK_DIR
uv run -m app --port 8888
