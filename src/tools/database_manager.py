from sqlite3 import connect, Error

from .logging_manager import LoggingManager

class DatabaseManager:
    """
    Class responsible for creating and managing the connection to the SQLite database.

    Arguments:
    db_file (str): The SQLite database file.

    Attributes:
    conn (sqlite3.Connection): The database connection instance.

    Raises:
    ValueError: If it is not possible to connect to the database.
    """

    def __init__(self, db_file):
        self.db_file = db_file
        self.conn = None
        self.logger = LoggingManager(logger_name='DatabaseManager').get_logger()
        self._create_connection()

    def _create_connection(self):
        """ Establishes the connection to the database. """
        try:
            self.conn = connect(self.db_file)
            self.logger.info(f"Connected to the database {self.db_file} successfully")
        except Error as e:
            self.logger.error(f"Error connecting to the database: {e}")
            raise ValueError(f"Error connecting to the database: {e}")

    def create_table(self, create_table_sql):
        """ Creates a table in the database using the provided SQL statement. """
        try:
            with self.conn:
                self.conn.execute(create_table_sql)
            self.logger.info("Table created successfully")
        except Error as e:
            self.logger.error(f"Error creating table: {e}")

    def insert_data(self, insert_sql, data):
        """ Inserts data into the table using the provided SQL statement and data. """
        try:
            with self.conn:
                self.conn.execute(insert_sql, data)
            self.logger.info("Data inserted successfully")
        except Error as e:
            self.logger.error(f"Error inserting data: {e}")

    def update_data(self, update_sql, data):
        """ Updates data in the table using the provided SQL statement and data. """
        try:
            with self.conn:
                self.conn.execute(update_sql, data)
            self.logger.info("Data updated successfully")
        except Error as e:
            self.logger.error(f"Error updating data: {e}")

    def delete_data(self, delete_sql, data):
        """ Deletes data from the table using the provided SQL statement and data. """
        try:
            with self.conn:
                self.conn.execute(delete_sql, data)
            self.logger.info("Data deleted successfully")
        except Error as e:
            self.logger.error(f"Error deleting data: {e}")

    def select_data(self, select_sql, data=None):
        """ Selects data from the table using the provided SQL statement. """
        try:
            with self.conn:
                cursor = self.conn.execute(select_sql, data) if data else self.conn.execute(select_sql)
                rows = cursor.fetchall()
                self.logger.info("Data retrieved successfully")
                return rows
        except Error as e:
            self.logger.error(f"Error retrieving data: {e}")
            return None

    def close_connection(self):
        """ Closes the database connection. """
        if self.conn:
            self.conn.close()
            self.logger.info("Database connection closed")
