<<<<<<< HEAD
export PYTHONPATH=./src
python src/webapp/api.py
=======
#!/bin/bash
NCORES=$(nproc)
NWORKERS=$(((2*$NCORES)+1))
if [[ $NWORKERS > 12 ]]; then
    NWORKERS=12
fi

echo $(which python)
echo $(python --version)
gunicorn --bind=0.0.0.0 --timeout=600 -w=$NWORKERS --chdir src/ webapp.api:app
>>>>>>> 461201b6631e3b921153515e14c2a7b3625234d5
