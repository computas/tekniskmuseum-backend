#!/bin/bash
# Start webapp or run tests

# compute number of gunicorn workers
NCORES=$(nproc)
NWORKERS=$(((2*$NCORES)+1))
if [[ $NWORKERS > 12 ]]; then
    NWORKERS=12
fi

# check if test run
while [[ "$#" > 0 ]]; do
    case $1 in
        -t | --test) test=true; shift ;;
        *) echo "Unexpected option: $1"; exit 1 ;;
    esac
    shift
done


if [[ $test = true ]]; then
    python -m pytest
    exit
fi


echo $(which python)
echo $(python --version)
gunicorn --bind=0.0.0.0 --timeout=600 -w=$NWORKERS --chdir src/ webapp.api:app
