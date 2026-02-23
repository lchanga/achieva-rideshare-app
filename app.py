from flask import Flask, jsonify
from database import get_db_connection

app = Flask(__name__)

@app.route('/')
def home():
    return "Achieva Rideshare API is officially online!"

@app.route('/test-db')
def test_connection():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Im just running a simple query to see if it connects with achieva database
        cursor.execute("SELECT @@VERSION") 
        row = cursor.fetchone()
        conn.close()
        
        return jsonify({
            "status": "Success!",
            "database_version": row[0],
            "message": "The bridge to Ryan's SQL server is working."
        })
    except Exception as e:
        return jsonify({
            "status": "Error",
            "error_details": str(e)
        })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)