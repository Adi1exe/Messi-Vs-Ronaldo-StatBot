import sqlite3
import datetime

def initialize_test_data():
    """Initialize the database with test data for Messi vs Ronaldo statistics"""
    
    print("Initializing database with test data...")
    
    # Create/connect to SQLite database
    conn = sqlite3.connect('football_stats.db')
    cursor = conn.cursor()
    
    # Create tables if they don't exist
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY,
        name TEXT UNIQUE,
        display_name TEXT
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS stats (
        id INTEGER PRIMARY KEY,
        category_id INTEGER,
        messi_value TEXT,
        ronaldo_value TEXT,
        description TEXT,
        last_updated TEXT,
        FOREIGN KEY (category_id) REFERENCES categories (id)
    )
    ''')
    
    # Clear existing data
    cursor.execute("DELETE FROM stats")
    cursor.execute("DELETE FROM categories")
    
    # Insert categories
    categories = [
        (1, "goals", "Goals"),
        (2, "assists", "Assists"),
        (3, "trophies", "Trophies"),
        (4, "awards", "Awards"),
        (5, "international", "International Performance"),
        (6, "club", "Club Performance"),
        (7, "career", "Career Statistics"),
        (8, "hat_tricks", "Hat Tricks"),
        (9, "free_kicks", "Free Kicks"),
        (10, "penalties", "Penalties")
    ]
    
    cursor.executemany("INSERT INTO categories (id, name, display_name) VALUES (?, ?, ?)", categories)
    
    # Insert stats
    last_updated = datetime.datetime.now().strftime("%Y-%m-%d")
    
    stats = [
        # Goals
        (1, 1, "Total Career Goals", "821", "837", last_updated),
        (2, 1, "Club Goals", "701", "713", last_updated),
        (3, 1, "International Goals", "120", "124", last_updated),
        (4, 1, "Champions League Goals", "129", "140", last_updated),
        
        # Assists
        (5, 2, "Total Career Assists", "338", "258", last_updated),
        (6, 2, "Club Assists", "305", "226", last_updated),
        (7, 2, "International Assists", "33", "32", last_updated),
        
        # Trophies
        (8, 3, "Total Major Trophies", "42", "34", last_updated),
        (9, 3, "Champions League Titles", "4", "5", last_updated),
        (10, 3, "League Titles", "12", "7", last_updated),
        (11, 3, "World Cup Titles", "1", "0", last_updated),
        (12, 3, "Copa America Titles", "1", "0", last_updated),
        (13, 3, "European Championship Titles", "0", "1", last_updated),
        
        # Awards
        (14, 4, "Ballon d'Or", "8", "5", last_updated),
        (15, 4, "FIFA Best Player", "6", "5", last_updated),
        (16, 4, "Golden Boot", "6", "4", last_updated),
        (17, 4, "World Cup Golden Ball", "2", "0", last_updated),
        
        # International
        (18, 5, "World Cup Goals", "13", "8", last_updated),
        (19, 5, "World Cup Appearances", "5", "5", last_updated),
        (20, 5, "Major International Trophies", "2", "1", last_updated),
        (21, 5, "International Goals", "120", "124", last_updated),
        (22, 5, "International Assists", "33", "32", last_updated),
        
        # Club Performance
        (23, 6, "Champions League Goals", "129", "140", last_updated),
        (24, 6, "Champions League Assists", "40", "42", last_updated),
        (25, 6, "League Goals", "496", "498", last_updated),
        (26, 6, "League Assists", "224", "153", last_updated),
        
        # Career Stats
        (27, 7, "Games Played", "1050", "1178", last_updated),
        (28, 7, "Goals per Game", "0.78", "0.71", last_updated),
        (29, 7, "Assists per Game", "0.32", "0.22", last_updated),
        (30, 7, "Career Hat-tricks", "56", "61", last_updated),
        
        # Hat Tricks
        (31, 8, "Career Hat Tricks", "56", "61", last_updated),
        (32, 8, "International Hat Tricks", "9", "10", last_updated),
        (33, 8, "Club Hat Tricks", "47", "51", last_updated),
        
        # Free Kicks
        (34, 9, "Free Kick Goals", "65", "58", last_updated),
        (35, 9, "Club Free Kicks", "58", "53", last_updated),
        (36, 9, "International Free Kicks", "7", "5", last_updated),
        
        # Penalties
        (37, 10, "Penalty Goals", "110", "142", last_updated),
        (38, 10, "Penalty Conversion Rate", "78%", "84%", last_updated),
        (39, 10, "Missed Penalties", "31", "29", last_updated)
    ]
    
    cursor.executemany("""
        INSERT INTO stats 
        (id, category_id, description, messi_value, ronaldo_value, last_updated)
        VALUES (?, ?, ?, ?, ?, ?)
    """, stats)
    
    # Commit changes and close connection
    conn.commit()
    conn.close()
    
    print("Database initialization completed.")
    return True

if __name__ == "__main__":
    initialize_test_data()