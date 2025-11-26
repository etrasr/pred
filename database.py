import sqlite3
import json
import logging
from datetime import datetime, timedelta
import os

logger = logging.getLogger(__name__)

class PredictionDatabase:
    def __init__(self):
        self.db_path = 'keno_predictions.db'
        self.init_database()
    
    def init_database(self):
        """Initialize database tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Draws history
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS draws (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                draw_time TIMESTAMP,
                numbers TEXT,
                round_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Number statistics
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS number_stats (
                number INTEGER PRIMARY KEY,
                total_appearances INTEGER DEFAULT 0,
                last_seen TIMESTAMP,
                hot_streak INTEGER DEFAULT 0,
                cold_streak INTEGER DEFAULT 0,
                frequency_1h REAL DEFAULT 0,
                frequency_24h REAL DEFAULT 0
            )
        ''')
        
        # Prediction history
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                prediction_time TIMESTAMP,
                very_high_numbers TEXT,
                high_numbers TEXT,
                confidence_score REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("✅ Prediction database initialized")
    
    def save_draw(self, numbers: list, round_id: str = None):
        """Save a new draw to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            draw_time = datetime.now()
            numbers_json = json.dumps(numbers)
            
            cursor.execute('''
                INSERT INTO draws (draw_time, numbers, round_id)
                VALUES (?, ?, ?)
            ''', (draw_time, numbers_json, round_id))
            
            # Update number statistics
            for number in numbers:
                cursor.execute('''
                    INSERT OR REPLACE INTO number_stats 
                    (number, total_appearances, last_seen, hot_streak, cold_streak)
                    VALUES (
                        ?, 
                        COALESCE((SELECT total_appearances FROM number_stats WHERE number = ?), 0) + 1,
                        ?,
                        CASE 
                            WHEN (SELECT last_seen FROM number_stats WHERE number = ?) IS NOT NULL THEN
                                CASE WHEN julianday(?) - julianday((SELECT last_seen FROM number_stats WHERE number = ?)) < 0.1 
                                THEN COALESCE((SELECT hot_streak FROM number_stats WHERE number = ?), 0) + 1
                                ELSE 1 END
                            ELSE 1
                        END,
                        CASE 
                            WHEN (SELECT last_seen FROM number_stats WHERE number = ?) IS NOT NULL THEN
                                CASE WHEN julianday(?) - julianday((SELECT last_seen FROM number_stats WHERE number = ?)) >= 1 
                                THEN COALESCE((SELECT cold_streak FROM number_stats WHERE number = ?), 0) + 1
                                ELSE 0 END
                            ELSE 0
                        END
                    )
                ''', (number, number, draw_time, number, draw_time, number, number, number, draw_time, number, number))
            
            conn.commit()
            conn.close()
            logger.info(f"✅ Draw saved: {numbers}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error saving draw: {e}")
            return False
    
    def get_recent_draws(self, hours: int = 48, limit: int = 100):
        """Get recent draws"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            time_threshold = datetime.now() - timedelta(hours=hours)
            
            cursor.execute('''
                SELECT draw_time, numbers FROM draws 
                WHERE draw_time > ? 
                ORDER BY draw_time DESC 
                LIMIT ?
            ''', (time_threshold, limit))
            
            results = cursor.fetchall()
            draws = []
            
            for draw_time, numbers_json in results:
                numbers = json.loads(numbers_json)
                draws.append({
                    'time': draw_time,
                    'numbers': numbers
                })
            
            conn.close()
            return draws
            
        except Exception as e:
            logger.error(f"❌ Error getting recent draws: {e}")
            return []
    
    def get_number_stats(self):
        """Get comprehensive number statistics"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Calculate frequencies
            cursor.execute('''
                SELECT 
                    ns.number,
                    ns.total_appearances,
                    ns.last_seen,
                    ns.hot_streak,
                    ns.cold_streak,
                    -- Frequency in last 1 hour
                    (SELECT COUNT(*) FROM draws d 
                     WHERE json_each.value = ns.number 
                     AND d.draw_time > datetime('now', '-1 hour')) as freq_1h,
                    -- Frequency in last 24 hours
                    (SELECT COUNT(*) FROM draws d 
                     WHERE json_each.value = ns.number 
                     AND d.draw_time > datetime('now', '-24 hours')) as freq_24h
                FROM number_stats ns
                ORDER BY ns.total_appearances DESC
            ''')
            
            stats = {}
            for row in cursor.fetchall():
                number, appearances, last_seen, hot_streak, cold_streak, freq_1h, freq_24h = row
                stats[number] = {
                    'appearances': appearances,
                    'last_seen': last_seen,
                    'hot_streak': hot_streak,
                    'cold_streak': cold_streak,
                    'frequency_1h': freq_1h,
                    'frequency_24h': freq_24h
                }
            
            conn.close()
            return stats
            
        except Exception as e:
            logger.error(f"❌ Error getting number stats: {e}")
            return {}
    
    def save_prediction(self, very_high: list, high: list, confidence: float):
        """Save prediction to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO predictions (prediction_time, very_high_numbers, high_numbers, confidence_score)
                VALUES (?, ?, ?, ?)
            ''', (datetime.now(), json.dumps(very_high), json.dumps(high), confidence))
            
            conn.commit()
            conn.close()
            logger.info("✅ Prediction saved to database")
            return True
        except Exception as e:
            logger.error(f"❌ Error saving prediction: {e}")
            return False
    
    def get_total_draws(self):
        """Get total number of draws"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM draws')
            count = cursor.fetchone()[0]
            conn.close()
            return count
        except:
            return 0
