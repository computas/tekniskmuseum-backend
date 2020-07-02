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
        -t | --test)        test=true;
                            shift ;;
        -h | --help)        help=true;
                            shift ;;
        -w=* | --workers=*) NWORKERS="${1#*=}";
                            shift ;;
        *)                  echo "Unexpected option: $1, use -h for help";
                            exit 1 ;;
    esac
    shift
done

usage="Script to start webapp with gunicorn.
Options:
    -h, --help      Print this help page.
    -t, --test      Run unit tests with pytest.
    -w, --workers   Specify number of gunicorn workers.
                    Recommended values are 3-12 workers.
"

if [[ $test = true ]]; then
    cd src/
    python -m pytest
    exit
elif [[ $help = true ]]; then
    echo "$usage"
    exit
fi

echo "===================================="
echo "       Teknisk museum backend       "
echo "===================================="
echo $(which python)
echo $(python --version)
echo "Number processing units: $NCORES"
echo "Number of workers: $NWORKERS"
echo "------------------------------------"
gunicorn --bind=0.0.0.0 --timeout=600 -w=$NWORKERS --chdir src/ webapp.api:app
