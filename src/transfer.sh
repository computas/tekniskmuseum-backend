cd "$(dirname "$0")"
export PYTHONPATH="${PYTHONPATH}:$(pwd):$(pwd)/preprocessing"
python3 preprocessing/data_migration.py snowman