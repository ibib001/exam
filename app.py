from sqlalchemy import create_engine
from sqlalchemy_utils import database_exists, create_database
from controllers import app, db
import os

# Define your main database URL
DATABASE_URL = app.config['SQLALCHEMY_DATABASE_URI']

# Create an engine for the default connection (i.e., `postgres` db)
default_engine = create_engine(DATABASE_URL)

if __name__ == "__main__":
    # Check if the target database exists
    if not database_exists(DATABASE_URL):
        # If the database doesn't exist, create it
        create_database(DATABASE_URL)
        print(f"Database 'secure_api' created.")

    # Now, proceed with your app's database operations
    with app.app_context():
        db.create_all()  # Create all tables within the newly created database
        print("Tables created in the database.")

    app.run(debug=True)
