#!/bin/bash
# Start webapp or run tests

# compute number of gunicorn workers
NCORES=$(nproc)
NWORKERS=$(((2*$NCORES)+1))
if [[ $NWORKERS > 12 ]]; then
    NWORKERS=12
fi

# Get console widtg
cols=$(tput cols)

# Parse flags
while [[ "$#" > 0 ]]; do
    case $1 in
        -l | --local)       local=true;
                            shift ;;
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

# Help string
usage="Script to start webapp with gunicorn.
Options:
    -h, --help      Print this help page
    -t, --test      Run unit tests with pytest
    -l, --local     Only expose 127.0.0.1
    -w, --workers   Specify number of gunicorn workers,
                    recommended values are 3-12 workers"

# print headline with first argument
printHeadline() {
    wordlength=${#1}
    padlength=$(( ($cols - $wordlength - 2) / 2 ))
    printf %"$padlength"s | tr " " "="
    printf " $1 "
    printf %"$padlength"s | tr " " "="
}

# print line with terminal width
printline() {
    printf %"$cols"s | tr " " "-"
}

if [[ $test = true ]]; then
    cd src/
    printHeadline "flake8"
    flake8
    python -m pytest
    exit
elif [[ $help = true ]]; then
    echo "$usage"
    exit
fi

# Print some info
printHeadline "Teknisk museum backend"
echo "
$(python --version)
$(which python)
Number processing units: $NCORES
Number of workers: $NWORKERS"
printline

# Local only exposes 127.0.0.1
if [[ $local = true ]]; then
    gunicorn --timeout=600 -w=$NWORKERS --chdir src/ webapp.api:app
else
    gunicorn --bind=0.0.0.0 --timeout=600 -w=$NWORKERS --chdir src/ webapp.api:app
fi
printline
