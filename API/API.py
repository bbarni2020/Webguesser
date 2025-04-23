import sqlite3
import pandas as pd
import json
from datetime import date, datetime, timedelta
import requests
from flask import Flask, request, abort, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import firebase_admin
from firebase_admin import credentials, auth
from flask_cors import CORS
import uuid
import random

conn = sqlite3.connect('database.db', check_same_thread=False)
cur = conn.cursor()

cred = credentials.Certificate("key.json")
firebase_admin.initialize_app(cred)

app = Flask(__name__)
CORS(app)
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["1 per second"]
)

API_KEY = ''

def get_db_connection():
    conn = sqlite3.connect('database.db', check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys = ON;')
    return conn

@app.route('/generate_test_uid', methods=['GET'])
@limiter.limit("1 per second")
def generate_test_uid():
    try:
        test_uid = f"test-{uuid.uuid4().hex[:16]}"
        test_email = f"test-{uuid.uuid4().hex[:8]}@example.com"
        test_username = f"tester-{uuid.uuid4().hex[:6]}"
        
        points = random.randint(0, 1000)
        matches = random.randint(0, 10)
        description = "This is a test user for API testing"
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("BEGIN EXCLUSIVE")
        
        cursor.execute("SELECT * FROM users WHERE uid = ?", (test_uid,))
        existing_user = cursor.fetchone()
        
        if existing_user is None:
            cursor.execute("""
            INSERT INTO users (uid, email, username, point, matches, last_match, created, leaderboard, description, active) VALUES
            (?, ?, ?, ?, ?, ?, ?, 1, ?, 1)
            """, (test_uid, test_email, test_username, points, matches, date.today(), date.today(), description))
            
            cursor.execute("""
            INSERT INTO games (uid, round, points) VALUES
            (?, 1, 0)
            """, (test_uid,))
            
            conn.commit()
            
            return jsonify({
                "message": "Test UID generated successfully",
                "uid": test_uid,
                "email": test_email,
                "username": test_username,
                "points": points,
                "matches": matches,
                "note": "This test user can be used to test the API endpoints"
            }), 200
        else:
            return jsonify({
                "message": "Test UID already exists",
                "uid": test_uid
            }), 200
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

@app.route('/match_new', methods=['GET'])
@limiter.limit("1 per second")
def match_new():
    uid = request.args.get('uid')
    if not uid:
        return jsonify({"error": "UID is required"}), 400
    result = auth.get_users([
        auth.UidIdentifier(uid),
    ])
    if len(result.users) != 0:
        for user in result.users:
            email_of_usr = user.email
    else:
        return jsonify({"error": "User not found"}), 404
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("BEGIN EXCLUSIVE")

        cursor.execute("SELECT * FROM users WHERE uid = ?", (uid,))
        user = cursor.fetchone()

        if user is None:
            cursor.execute("""
            INSERT INTO users (uid, email, username, point, matches, last_match, created, leaderboard, description, active) VALUES
            (?, ?, ?, 0, 0, '2000-01-01', ?, 1, '', 1)
            """, (uid, email_of_usr, email_of_usr, date.today()))
            conn.commit()
            cursor.execute("SELECT * FROM users WHERE uid = ?", (uid,))
            user = cursor.fetchone()

        if user['active'] != 1:
            return jsonify({"error": "ban"}), 403

        cursor.execute("SELECT * FROM games WHERE uid = ?", (uid,))
        game = cursor.fetchone()

        if game is None:
            cursor.execute("""
            INSERT INTO games (uid, round, points) VALUES
            (?, 1, 0)
            """, (uid,))
            conn.commit()
            return jsonify({"match": uid, "points": 0, "round": 1})
        else:
            return jsonify({"match": uid, "points": game['points'], "round": str(int(game['round']))}), 200
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

@app.route('/update_match', methods=['GET'])
@limiter.limit("1 per second")
def update_game():
    cheat = False
    uid = request.args.get('uid')
    points = request.args.get('points')
    round = request.args.get('round')

    if not uid or points is None or round is None:
        return jsonify({"error": "notenough"}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("BEGIN EXCLUSIVE")

        cursor.execute("SELECT * FROM games WHERE uid = ?", (uid,))
        game = cursor.fetchone()

        cursor.execute("SELECT * FROM users WHERE uid = ?", (uid,))
        userdata = cursor.fetchone()

        if game is None:
            return jsonify({"error": "notmatch"}), 404

        if int(points) <= 1000:
            new_points = game['points'] + int(points)
        else:
            cheat = True

        if game['round'] == int(round) and game['round'] < 6:
            new_round = game['round'] + 1
        else:
            cheat = True

        if not cheat:
            cursor.execute("""
                UPDATE games
                SET points = ?, round = ?
                WHERE uid = ?
            """, (new_points, new_round, uid))

            if new_round >= 6:
                cursor.execute("SELECT point FROM users WHERE uid = ?", (uid,))
                user = cursor.fetchone()
                total_points = user['point'] + new_points

                cursor.execute("""
                    UPDATE users
                    SET last_match = ?, point = ?, matches = matches + 1
                    WHERE uid = ?
                """, (date.today(), total_points, uid))
                cursor.execute("DELETE FROM games WHERE uid = ?", (uid,))
                conn.commit()
                return jsonify({"status": "end"}), 200
            conn.commit()
            return jsonify({"uid": uid, "points": new_points, "round": new_round}), 200

        else:
            cursor.execute("""
                UPDATE users
                SET active = 0
                WHERE uid = ?
            """, (uid,))
            conn.commit()

            url = 'http://localhost:2301/send_message'
            data = {
                'uid': uid,
                'user_name': userdata['username'],
                'email': userdata['email']
            }
            response = requests.post(url, json=data)

            if response.status_code == 200:
                print('Message sent successfully')
            else:
                print(f'Failed to send message: {response.json()}')

            return jsonify({"error": "cheat"}), 400
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

@app.route('/update_profile', methods=['POST'])
@limiter.limit("1 per second")
def update_profile():
    data = request.get_json()
    uid = data.get('uid')
    leaderboard = data.get('leaderboard')
    username = data.get('username')
    description = data.get('description')
    if not uid or leaderboard is None or not username or not description:
        return jsonify({"error": "notenough"}), 400

    if leaderboard != '1' and leaderboard != '0':
        return jsonify({"error": "wrong"}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("BEGIN EXCLUSIVE")

        cursor.execute("SELECT active FROM users WHERE uid = ?", (uid,))
        user = cursor.fetchone()

        if user is None:
            return jsonify({"error": "User not found"}), 404

        if user['active'] != 1:
            return jsonify({"error": "User is not active"}), 403

        cursor.execute("""
            UPDATE users
            SET leaderboard = ?, username = ?, description = ?
            WHERE uid = ?
        """, (leaderboard, username, description, uid))

        conn.commit()
        return jsonify({"message": "success"}), 200
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

@app.route('/get_profile', methods=['GET'])
@limiter.limit("1 per second")
def get_profile():
    uid = request.args.get('uid')

    if not uid:
        return jsonify({"error": "UID is required"}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("BEGIN EXCLUSIVE")

        cursor.execute("""
            SELECT email, username, point, matches, last_match, created, leaderboard, description
            FROM users
            WHERE uid = ?
        """, (uid,))
        user = cursor.fetchone()

        if user is None:
            result = auth.get_users([auth.UidIdentifier(uid)])
            if len(result.users) != 0:
                for firebase_user in result.users:
                    email_of_usr = firebase_user.email
                cursor.execute("""
                    INSERT INTO users (uid, email, username, point, matches, last_match, created, leaderboard, description, active) VALUES
                    (?, ?, ?, 0, 0, '2000-01-01', ?, 1, '', 1)
                """, (uid, email_of_usr, email_of_usr, date.today()))
                conn.commit()
                cursor.execute("""
                    SELECT email, username, point, matches, last_match, created, leaderboard, description
                    FROM users
                    WHERE uid = ?
                """, (uid,))
                user = cursor.fetchone()
            else:
                return jsonify({"error": "User not found"}), 404

        profile_info = {
            "email": user["email"],
            "username": user["username"],
            "point": user["point"],
            "matches": user["matches"],
            "last_match": user["last_match"],
            "created": user["created"],
            "leaderboard": user["leaderboard"],
            "description": user["description"]
        }

        return jsonify(profile_info), 200
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

@app.route('/user', methods=['GET'])
@limiter.limit("1 per second")
def get_user_info():
    username = request.args.get('username')

    if not username:
        return jsonify({"error": "Username is required"}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("BEGIN EXCLUSIVE")

        cursor.execute("""
            SELECT username, description, last_match, point
            FROM users
            WHERE username = ?
        """, (username,))
        user = cursor.fetchone()

        if user is None:
            return jsonify({"error": "User not found"}), 404

        user_info = {
            "username": user["username"],
            "description": user["description"],
            "last_match": user["last_match"],
            "point": user["point"]
        }

        return jsonify(user_info), 200
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

@app.route('/is_active', methods=['GET'])
@limiter.limit("1 per second")
def is_active():
    uid = request.args.get('uid')

    if not uid:
        return jsonify({"error": "notenough"}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("BEGIN EXCLUSIVE")

        cursor.execute("SELECT active FROM users WHERE uid = ?", (uid,))
        user = cursor.fetchone()

        if user is None:
            return jsonify({"error": "nouser"}), 404

        is_active = user["active"] == 1

        return jsonify({"uid": uid, "is_active": is_active}), 200
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

@app.route('/unlock', methods=['POST'])
@limiter.limit("1 per second")
def update_active():
    api_key = request.headers.get('Authorization')
    if api_key != f'Bearer {API_KEY}':
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json()
    uid = data.get('uid')
    active = data.get('active')
    if not uid or active not in [0, 1]:
        return jsonify({"error": "UID and valid active status are required"}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("BEGIN EXCLUSIVE")

        cursor.execute("SELECT * FROM users WHERE uid = ?", (uid,))
        user = cursor.fetchone()

        if user is None:
            return jsonify({"error": "User not found"}), 404

        cursor.execute("""
            UPDATE users
            SET active = ?
            WHERE uid = ?
        """, (active, uid))

        conn.commit()
        return jsonify({"message": f"User {'activated' if active == 1 else 'deactivated'} successfully"}), 200
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

@app.route('/')
def home():
    return '''
    <html>
        <head>
            <title>Webguesser API</title>
        </head>
        <body>
            <a href="https://webguesser.masterbros.dev/API">Go to Documentation</a>
            <script>
                window.location.href = "https://webguesser.masterbros.dev/API";
            </script>
        </body>
    </html>
    '''

if __name__ == '__main__':
    app.run(port=5640)
