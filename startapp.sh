#!/bin/bash
NCORES=$(nproc)
NWORKERS=$(((2*$NCORES)+1))
if [[ $NWORKERS > 12 ]]; then
    NWORKERS=12
fi

echo $(which python)
echo $(python --version)
gunicorn --bind=0.0.0.0 --timeout=600 -w=$NWORKERS --chdir src/ webapp.api:app
