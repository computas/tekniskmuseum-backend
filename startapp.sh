#!/bin/bash
# This script serves as the main interface to the app

# Compute number of gunicorn workers
ncores=$(nproc)
nworkers=$(((2*$ncores)+1))
if [[ $nworkers -gt 12 ]]; then
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

# print headline with text. Optional first argument determines color.
printHeadline() {
    # use green/red text if first argumnet is 'green' or 'red'
    if [[ $1 = green ]]; then
        printf '\e[32m'
        shift
    elif [[ $1 = red ]]; then
        printf '\e[31m'
        shift
    fi
    printf '\e[1m'
    wordlength=${#1}
    padlength=$(( ($cols - $wordlength - 2) / 2 ))
    printf %"$padlength"s | tr " " "="
    printf " $1 "
    printf %"$padlength"s | tr " " "="
    printf '\e[0m\n'
}

# print line with terminal width
printline() {
    printf '\e[1m'
    printf %"$cols"s | tr " " "-"
    printf '\e[0m\n'
}

runTests() {
    printHeadline 'Teknisk Museum Backend'
    printf "$(python --version)\n$(which python)\n"

    cd src/
    if [[ ! -z "$keystring" ]]; then
        python runTests.py --keys="$keystring"
        exit
    else
        printHeadline 'PEP8 linting'
        flake8 
        # check if linting is successfull
        if [[ $? -eq 0 ]]; then
            printHeadline green 'no linting errors'
        else
            printHeadline red 'linting failed'
        fi
        python -m pytest
    fi
}

# Parse flags
while [[ "$#" -gt 0 ]]; do
    case $1 in
        -h | --help)        echo "$usage";
                            exit 0;;
        --keys=*)           keystring="${1#*=}";
                            shift;;
        -t | --test)        runTests;
                            exit 0;;
        -d | --debug)       debug=true;
                            nworkers=1;
                            shift;;
        -w=* | --workers=*) nworkers="${1#*=}";
                            shift;;
        *)                  echo "Unexpected option: $1, use -h for help";
                            exit 1;;
    esac
done

# Print some info
printHeadline 'Teknisk Museum backend'
echo "$(python --version)
$(which python)
Number processing units: $ncores
Number of workers: $nworkers"



# Default settings and entry point to flask
default_settings="--timeout=600 -w=1 --chdir src/ main:app"
logfile='/home/LogFiles/flaskapp.log'

# Database migration
printHeadline 'Database Migration'
export FLASK_APP=main.py  # Replace with the entry point of your Flask app

# Initialize migrations folder if not initialized
if [[ ! -d "migrations" ]]; then
    echo "Initializing migration directory..."
    flask db init
fi

current_version=$(flask db current)  # Get the current migration version of the database
latest_version=$(flask db heads)     # Get the latest migration version available

if [[ "$current_version" != "$latest_version" ]]; then
    echo "New migration available. Running migration..."
    flask db migrate -m "Auto migration via script"
    #flask db upgrade
else
    echo "Database is up to date. No migration needed."
fi


if [[ $debug = true ]]; then
    printHeadline red 'Debug mode'
    echo 'Debug mode activated. Gunicorn is reloaded on code changes.'
    export DEBUG=true
    printline
    gunicorn --reload $default_settings
elif [[ $IS_PRODUCTION = true ]]; then
    gunicorn --bind=0.0.0.0 --log-file=$logfile $default_settings
    echo "Logs written to: $logfile"
else
    printline
    gunicorn --bind=0.0.0.0 $default_settings
fi

printline