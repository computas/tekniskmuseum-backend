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
    -h, --help      Print this help page.
    -t, --test      Run linter and unit tests.
    -d, --debug     Gunicorn reloads on code change,
                    number of workers set to 1,
                    and only 127.0.0.1 is exposed.
    -w, --workers   Specify number of gunicorn workers,
                    recommended values are 3-12 workers.'

# print headline with first argument
printHeadline() {
    # use green text if first argumnet is 'green'
    if [[ $1 = green ]]; then
        printf '\e[32m'
        shift
    elif [[ $1 = red ]]; then
        printf '\e[31m'
        shift
    else
        printf '\e[1m'
    fi
    wordlength=${#1}
    padlength=$(( ($cols - $wordlength - 2) / 2 ))
    printf %"$padlength"s | tr " " "="
    printf "\e[1m $1 \e[21m"
    printf %"$padlength"s | tr " " "="
    printf '\e[0m\n'
}

# print line with terminal width
printline() {
    printf '\e[1m'
    printf %"$cols"s | tr " " "-"
    printf '\e[0m\n'
}

# Parse flags
while [[ "$#" > 0 ]]; do
    case $1 in
        -t | --test)        test=true;
                            shift ;;
        -h | --help)        help=true;
                            shift ;;
        -d | --debug)       debug=true;
                            nworkers=1;
                            shift ;;
        -w=* | --workers=*) nworkers="${1#*=}";
                            shift ;;
        *)                  echo "Unexpected option: $1, use -h for help";
                            exit 1 ;;
    esac
done

if [[ $test = true ]]; then
    cd src/
    printHeadline 'PEP8 linting'
    flake8 && printHeadline green 'no linting errors'
    python -m pytest
    exit
elif [[ $help = true ]]; then
    echo "$usage"
    exit
fi

# Print some info
printHeadline 'Teknisk museum backend'
echo "$(python --version)
$(which python)
Number processing units: $ncores
Number of workers: $nworkers"

# Flask entrypoint
entrypoint='--chdir src/ webapp.api:app'

if [[ $debug = true ]]; then
    printHeadline red 'Debug mode'
    echo 'Debug mode activated. Gunicorn is reloaded on code changes.'
    printline
    gunicorn --reload -w=$nworkers $entrypoint
else
    printline
    gunicorn --bind=0.0.0.0 --timeout=600 -w=$nworkers $entrypoint
fi
printline
