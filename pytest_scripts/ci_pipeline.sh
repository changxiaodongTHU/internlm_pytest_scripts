#!/bin/bash

function print_usage() {
  RED='\033[0;31m'
  BLUE='\033[0;34m'
  BOLD='\033[1m'
  NONE='\033[0m'

  echo -e "${BOLD}bash ci_pipeline.sh${NONE} Command [Options]"

  echo -e "\n${RED}Command${NONE}:
    ${BLUE}internlm${NONE}: [case_name] default to run all cases in cases/internlm.json
    ${BLUE}usage${NONE}: display this message
  "
}

function internlm() {
  python ${CI_PROJECT_DIR}/pytest_scripts/tests/main.py \
    --test_json_file ${CI_PROJECT_DIR}/pytest_scripts/cases/internlm.json \
    --case_name  ""${@}
}

function imdeploy() {
  python ${CI_PROJECT_DIR}/pytest_scripts/tests/main.py \
    --test_json_file ${CI_PROJECT_DIR}/pytest_scripts/cases/imdeploy.json \
    --case_name  ""${@}
}


function main() {
  if [ -z $CI_PROJECT_DIR ]; then
    cd $( dirname ${BASH_SOURCE} )/..
    export CI_PROJECT_DIR=$(pwd)
    cd - > /dev/null
    echo ">>>>>>>>>>>>>>>>>>> CI_PROJECT_DIR is " $CI_PROJECT_DIR
  fi
  mkdir -p ${CI_PROJECT_DIR}/test_log
  pip install pytest --quiet
  local cmd=$1
  case $cmd in
    internlm)
      internlm ${@:2}
      ;;
    imdeploy)
      imdeploy ${@:2}
      ;;
    usage)
      print_usage
      ;;
    *)
      print_usage
      ;;
  esac
}


main $@
