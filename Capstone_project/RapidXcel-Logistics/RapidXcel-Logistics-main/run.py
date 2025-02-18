# run.py

from app import create_app
import logging

app = create_app()

if __name__ == '__main__':
    # Enable logging if needed
    logging.basicConfig(level=logging.INFO)
    app.logger.info("Starting the application...")

    # Run the app with debugging enabled
    app.run(debug=True)
