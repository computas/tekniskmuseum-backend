import os

if (
    not os.getenv("FLASK_RUN_FROM_CLI")
    and os.getenv("IS_PRODUCTION") == "true"
    and os.getenv("TESTING") != "true"
):
    from gevent import monkey

    monkey.patch_all()
from src import create_app

app, socketio = create_app()

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=8000)
