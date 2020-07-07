#!/bin/bash
# This script servers as the entrypoint to the app

# Compute number of gunicorn workers
ncores=$(nproc)
nworkers=$(((2*$ncores)+1))
if [[ $nworkers > 12 ]]; then
    nworkers=12
fi

# Get console width
cols=$(tput cols)

# Help string
usage='Script to start webapp with gunicorn.
Options:
    -h, --help      Print this help page
    -t, --test      Run unit tests with pytest
    -l, --local     Only expose 127.0.0.1
    -w, --workers   Specify number of gunicorn workers,
                    recommended values are 3-12 workers'

# print headline with first argument
printHeadline() {
    # use green text if first argumnet is 'green'
    if [[ $1 = green ]]; then
        printf '\e[32m'
        shift
    fi
    wordlength=${#1}
    padlength=$(( ($cols - $wordlength - 2) / 2 ))
    printf '\e[1m'
    printf %"$padlength"s | tr " " "="
    printf " $1 "
    printf %"$padlength"s | tr " " "="
}

# print line with terminal width
printline() {
    printf '\e[1m'
    printf %"$cols"s | tr " " "-"
}

# Parse flags
while [[ "$#" > 0 ]]; do
    case $1 in
        -l | --local)       local=true;
                            shift ;;
        -t | --test)        test=true;
                            shift ;;
        -h | --help)        help=true;
                            shift ;;
        -w=* | --workers=*) nworkers="${1#*=}";
                            shift ;;
        *)                  echo "Unexpected option: $1, use -h for help";
                            exit 1 ;;
    esac
done

if [[ $test = true ]]; then
    cd src/
    printHeadline 'flake8'
    flake8 && printHeadline green 'No linting errors'
    python -m pytest
    exit
elif [[ $help = true ]]; then
    echo "$usage"
    exit
fi

# Print some info
printHeadline 'Teknisk museum backend'
echo "
$(python --version)
$(which python)
Number processing units: $ncores
Number of workers: $nworkers"
printline

# Local only exposes 127.0.0.1
if [[ $local = true ]]; then
    gunicorn --timeout=600 -w=$nworkers --chdir src/ webapp.api:app
else
    gunicorn --bind=0.0.0.0 --timeout=600 -w=$nworkers --chdir src/ webapp.api:app
fi
printline
