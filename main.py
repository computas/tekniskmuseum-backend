from src import create_app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
else:
    app = create_app()
