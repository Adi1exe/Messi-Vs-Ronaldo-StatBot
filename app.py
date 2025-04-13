from flask import Flask, request, jsonify, render_template
import sqlite3
import re
from difflib import get_close_matches
import os

app = Flask(__name__)

def get_database_connection():
    conn = sqlite3.connect('football_stats.db')
    conn.row_factory = sqlite3.Row
    return conn

def refresh_data():
    from scraper import scrape_messi_vs_ronaldo
    return scrape_messi_vs_ronaldo()

def extract_intent(question):
    text = question.lower()
    categories = {
        "goals": ["goal", "goals", "score", "scored", "scoring", "scorer"],
        "assists": ["assist", "assists", "pass", "passes", "passing"],
        "trophies": ["trophy", "trophies", "title", "titles", "cup", "cups", "champion", "championship", "win", "won"],
        "awards": ["award", "awards", "ballon", "d'or", "golden", "boot", "player of the year"],
        "international": ["international", "country", "national", "nation", "world cup", "euro", "copa"],
        "club": ["club", "team", "barcelona", "real madrid", "manchester united", "juventus", "psg"],
        "career": ["career", "overall", "total", "statistic", "statistics"],
        "hat_tricks": ["hat trick", "hat-trick", "hattrick"],
        "free_kicks": ["free kick", "free-kick", "freekick"],
        "penalties": ["penalty", "penalties", "pen"],
    }

    comparison_patterns = [
        r"who has (more|better|higher|greater|most|bigger)",
        r"who scored (more|most)",
        r"who won (more|most)",
        r"compare",
        r"comparison",
        r"difference between",
        r"vs",
        r"versus",
    ]

    detected_category = None
    specific_stat = None
    comparison_type = "general"

    # Determine if query is about a specific player
    is_messi_specific = any(name in text for name in ["messi", "lionel"])
    is_ronaldo_specific = any(name in text for name in ["ronaldo", "cristiano"])
    
    # Check if it's a single player query
    if (is_messi_specific and not is_ronaldo_specific) or (is_ronaldo_specific and not is_messi_specific):
        comparison_type = "single_player"
        if is_messi_specific:
            comparison_type = "messi_only"
        else:
            comparison_type = "ronaldo_only"
    
    # If it's still not a single player query, check for comparison indicators
    else:
        for pattern in comparison_patterns:
            if re.search(pattern, text):
                comparison_type = "comparison"
                break

    for category, keywords in categories.items():
        for keyword in keywords:
            if keyword in text:
                detected_category = category
                break
        if detected_category:
            break
    
    # Handle direct questions
    direct_questions = {
        "who has world cup": ("trophies", "world_cup", "direct_question"),
        "who won world cup": ("trophies", "world_cup", "direct_question"),
        "who has champions league": ("trophies", "champions_league", "direct_question"),
        "who has more goals": ("goals", None, "comparison"),
        "who has more trophies": ("trophies", None, "comparison"),
        "who has more assists": ("assists", None, "comparison"),
        "who has ballon d'or": ("awards", "ballon_dor", "direct_question"),
    }
    
    for question_text, values in direct_questions.items():
        if question_text in text:
            detected_category, specific_stat, comparison_type = values
            break

    if "champions league" in text or "ucl" in text or "european" in text:
        specific_stat = "champions_league"
    elif "world cup" in text:
        specific_stat = "world_cup"
    elif "season" in text and re.search(r'\d{4}', text):
        years = re.findall(r'\d{4}', text)
        if len(years) >= 1:
            specific_stat = f"season_{years[0]}"
    elif "la liga" in text or "laliga" in text:
        specific_stat = "la_liga"
    elif "premier league" in text or "epl" in text:
        specific_stat = "premier_league"
    elif "serie a" in text:
        specific_stat = "serie_a"
    elif "ballon" in text or "d'or" in text:
        detected_category = "awards"
        specific_stat = "ballon_dor"
    elif "free kick" in text or "freekick" in text or "free-kick" in text:
        detected_category = "free_kicks"
    elif "penalty" in text or "penalties" in text:
        detected_category = "penalties"
    elif "hat trick" in text or "hat-trick" in text or "hattrick" in text:
        detected_category = "hat_tricks"

    return (detected_category, specific_stat, comparison_type)

def get_answer(category, specific_stat=None, comparison_type="general"):
    conn = get_database_connection()
    cursor = conn.cursor()

    try:
        if not category:
            return {
                "answer": "I can provide information about Messi and Ronaldo on goals, assists, trophies, awards, and more. What would you like to know?",
                "type": "clarification"
            }

        # Fetch all categories
        cursor.execute("SELECT name, id, display_name FROM categories")
        all_categories = cursor.fetchall()
        
        # Debug logging
        print(f"Looking for category: {category}")
        print(f"Available categories: {[row['name'] for row in all_categories]}")
        print(f"Comparison type: {comparison_type}")
        
        # Direct match first
        category_result = None
        for row in all_categories:
            if row['name'].lower() == category.lower():
                category_result = row
                break
        
        # If no direct match, try fuzzy match with more flexibility
        if not category_result and all_categories:
            category_names = [row['name'] for row in all_categories]
            matches = get_close_matches(category.lower(), category_names, n=3, cutoff=0.3)
            
            if matches:
                matched_name = matches[0]
                for row in all_categories:
                    if row['name'] == matched_name:
                        category_result = row
                        break
        
        # Still no match, try keyword matching
        if not category_result:
            for row in all_categories:
                if category.lower() in row['name'].lower() or row['name'].lower() in category.lower():
                    category_result = row
                    break
        
        # If still no match, check if any keyword from the database categories is in the user's query
        if not category_result:
            for row in all_categories:
                db_category_keywords = row['name'].lower().split('_')
                for keyword in db_category_keywords:
                    if keyword in category.lower() and len(keyword) > 2:  # Avoid short words
                        category_result = row
                        break
                if category_result:
                    break

        if not category_result:
            return {
                "answer": f"I don't have information about {category}. I can provide details about goals, assists, trophies, and other statistics.",
                "type": "not_found"
            }

        category_id = category_result['id']
        category_display = category_result['display_name']

        # Get all stats under the matched category
        cursor.execute("SELECT * FROM stats WHERE category_id = ?", (category_id,))
        stats = cursor.fetchall()

        if not stats:
            return {
                "answer": f"I don't have specific statistics about {category_display} right now.",
                "type": "not_found"
            }

        # Handle direct questions about specific stats
        if comparison_type == "direct_question" and specific_stat:
            matched_stat = None
            for stat in stats:
                if specific_stat.lower() in stat['description'].lower():
                    matched_stat = stat
                    break

            if matched_stat:
                messi_value = matched_stat['messi_value']
                ronaldo_value = matched_stat['ronaldo_value']
                description = matched_stat['description']

                if "world cup" in specific_stat.lower():
                    return {
                        "answer": f"Lionel Messi has won the World Cup (2022 with Argentina). Cristiano Ronaldo has not won a World Cup.",
                        "type": "direct_answer"
                    }
                elif "champions league" in specific_stat.lower():
                    return {
                        "answer": f"Both have won Champions League titles. Messi has {messi_value} Champions League titles, while Ronaldo has {ronaldo_value}.",
                        "type": "direct_answer"
                    }
                elif "ballon" in specific_stat.lower():
                    return {
                        "answer": f"Lionel Messi has won {messi_value} Ballon d'Or awards. Cristiano Ronaldo has won {ronaldo_value} Ballon d'Or awards.",
                        "type": "direct_answer"
                    }

        # Single player response
        if comparison_type in ["messi_only", "ronaldo_only"]:
            player_name = "Lionel Messi" if comparison_type == "messi_only" else "Cristiano Ronaldo"
            player_key = "messi" if comparison_type == "messi_only" else "ronaldo"
            
            result = f"{player_name}'s {category_display} Statistics:\n\n"
            for stat in stats:
                desc, value = stat['description'], stat[f'{player_key}_value']
                if desc:
                    result += f"• {desc}: {value}\n"
            
            return {
                "answer": result.strip(),
                "type": "single_player",
                "player": player_key,
                "category": category_display,
                "data": [dict(stat) for stat in stats]
            }

        # Specific stat comparison
        if specific_stat:
            matched_stat = None
            for stat in stats:
                if specific_stat.lower() in stat['description'].lower():
                    matched_stat = stat
                    break

            if matched_stat:
                messi_value = matched_stat['messi_value']
                ronaldo_value = matched_stat['ronaldo_value']
                description = matched_stat['description']

                comparison_text = ""
                if messi_value.isdigit() and ronaldo_value.isdigit():
                    m, r = int(messi_value), int(ronaldo_value)
                    if m > r:
                        comparison_text = f"Messi leads with {m} compared to Ronaldo's {r}."
                    elif r > m:
                        comparison_text = f"Ronaldo leads with {r} compared to Messi's {m}."
                    else:
                        comparison_text = f"Both Messi and Ronaldo have {m}."
                else:
                    comparison_text = f"Messi: {messi_value}, Ronaldo: {ronaldo_value}"

                return {
                    "answer": f"For {description}: {comparison_text}",
                    "data": {
                        "messi": messi_value,
                        "ronaldo": ronaldo_value,
                        "description": description
                    },
                    "type": "specific_comparison"
                }

        # General category comparison
        result = f"Comparing {category_display} between Messi and Ronaldo:\n\n"
        for stat in stats:
            m, r, desc = stat['messi_value'], stat['ronaldo_value'], stat['description']
            if desc:
                result += f"• {desc}: Messi ({m}) vs Ronaldo ({r})\n"

        return {
            "answer": result.strip(),
            "type": "category_comparison",
            "category": category_display,
            "data": [dict(stat) for stat in stats]
        }

    finally:
        conn.close()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/ask', methods=['POST'])
def ask_question():
    data = request.get_json()
    question = data.get('question', '')
    if not question:
        return jsonify({"error": "No question provided"}), 400

    category, specific_stat, comparison_type = extract_intent(question)
    answer = get_answer(category, specific_stat, comparison_type)
    answer['question'] = question
    return jsonify(answer)

@app.route('/refresh-data', methods=['POST'])
def api_refresh_data():
    try:
        success = refresh_data()
        if success:
            return jsonify({"status": "success", "message": "Data refreshed successfully"})
        else:
            return jsonify({"status": "error", "message": "Failed to refresh data"}), 500
    except Exception as e:
        return jsonify({"status": "error", "message": f"Error refreshing data: {str(e)}"}), 500

@app.route('/categories')
def get_categories():
    conn = get_database_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM categories")
        categories = cursor.fetchall()
        return jsonify([dict(c) for c in categories])
    finally:
        conn.close()

@app.route('/initialize-db', methods=['POST'])
def initialize_db():
    """Route for manually initializing the database with test data"""
    try:
        from db import initialize_test_data
        success = initialize_test_data()
        return jsonify({"status": "success", "message": "Database initialized successfully"})
    except Exception as e:
        return jsonify({"status": "error", "message": f"Error initializing database: {str(e)}"}), 500

def check_database():
    """Check if database exists and has data"""
    if not os.path.exists('football_stats.db'):
        print("Database file doesn't exist. Creating new database...")
        return False
    
    conn = get_database_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT COUNT(*) FROM categories")
        count = cursor.fetchone()[0]
        return count > 0
    except sqlite3.OperationalError:
        print("Database tables don't exist")
        return False
    finally:
        conn.close()

def create_database_tables():
    """Create database tables if they don't exist"""
    conn = get_database_connection()
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        display_name TEXT NOT NULL
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS stats (
        id INTEGER PRIMARY KEY,
        category_id INTEGER NOT NULL,
        description TEXT,
        messi_value TEXT,
        ronaldo_value TEXT,
        FOREIGN KEY (category_id) REFERENCES categories (id)
    )
    ''')
    
    conn.commit()
    conn.close()
    print("Database tables created")

if __name__ == '__main__':
    try:
        if not check_database():
            # Create tables first
            create_database_tables()
            
            # Try to scrape initial data
            print("Database is empty. Scraping initial data...")
            try:
                refresh_data()
                print("Initial data scraping completed")
            except Exception as e:
                print(f"Error scraping initial data: {str(e)}")
                print("You can initialize the database with test data using the /initialize-db endpoint")
    except Exception as e:
        print(f"Error during database setup: {str(e)}")

    app.run(debug=True)