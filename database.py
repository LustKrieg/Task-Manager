# Database
import sqlite3

DATABASE_NAME = "tasks.db"

def get_connection():
    conn = sqlite3.connect(DATABASE_NAME)
    return conn

get_connection()