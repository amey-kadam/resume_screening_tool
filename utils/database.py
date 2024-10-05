# utils/database.py
import sqlite3
from contextlib import contextmanager

DATABASE = 'resumes.db'

@contextmanager
def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    with get_db_connection() as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS resumes
            (id INTEGER PRIMARY KEY AUTOINCREMENT,
             filename TEXT NOT NULL,
             content TEXT NOT NULL,
             skills TEXT)
        ''')

def insert_resume(filename, content, skills):
    with get_db_connection() as conn:
        conn.execute('INSERT INTO resumes (filename, content, skills) VALUES (?, ?, ?)',
                     (filename, content, ','.join(skills)))
        conn.commit()

def search_resumes(query):
    with get_db_connection() as conn:
        cursor = conn.execute('SELECT * FROM resumes WHERE content LIKE ? OR skills LIKE ?',
                              (f'%{query}%', f'%{query}%'))
        return cursor.fetchall() 