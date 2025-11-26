import json
import logging
from datetime import datetime, timedelta
from gist_storage import GistStorage

logger = logging.getLogger(__name__)

class PredictionDatabase:
    def __init__(self):
        self.storage = GistStorage()
        self.data = self.storage.load_data()
        logger.info(f"✅ Database loaded from Gist. Draws: {len(self.data['draws'])}")
    
    def save_draw(self, numbers: list, round_id: str = None):
        """Save a new draw to database"""
        try:
            draw_time = datetime.now()
            draw_record = {
                "draw_time": draw_time.isoformat(),
                "numbers": numbers,
                "round_id": round_id or f"draw_{int(draw_time.timestamp())}"
            }
            
            # Add to draws list
            self.data["draws"].append(draw_record)
            
            # Update number statistics
            for number in numbers:
                if str(number) not in self.data["number_stats"]:
                    self.data["number_stats"][str(number)] = {
                        "total_appearances": 0,
                        "last_seen": None,
                        "hot_streak": 0,
                        "cold_streak": 0
                    }
                
                stats = self.data["number_stats"][str(number)]
                stats["total_appearances"] += 1
                stats["last_seen"] = draw_time.isoformat()
                
                # Simple streak tracking (you can enhance this)
                stats["hot_streak"] += 1
                stats["cold_streak"] = 0
            
            # Save to Gist
            success = self.storage.save_data(self.data)
            
            if success:
                logger.info(f"✅ Draw saved to Gist: {numbers}")
                logger.info(f"📊 Total draws: {len(self.data['draws'])}")
                return True
            else:
                logger.error("❌ Failed to save draw to Gist")
                return False
            
        except Exception as e:
            logger.error(f"❌ Error saving draw: {e}")
            return False
    
    def get_recent_draws(self, hours: int = 72, limit: int = 100):
        """Get recent draws"""
        try:
            recent_draws = []
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            for draw in reversed(self.data["draws"]):  # Start from most recent
                draw_time = datetime.fromisoformat(draw["draw_time"])
                if draw_time >= cutoff_time:
                    recent_draws.append({
                        'time': draw_time,
                        'numbers': draw['numbers']
                    })
                if len(recent_draws) >= limit:
                    break
            
            logger.info(f"📊 Retrieved {len(recent_draws)} recent draws")
            return recent_draws
            
        except Exception as e:
            logger.error(f"❌ Error getting recent draws: {e}")
            return []
    
    def get_number_stats(self):
        """Get comprehensive number statistics"""
        try:
            # Convert string keys to integers and add some calculated fields
            stats = {}
            total_draws = len(self.data["draws"])
            
            for num_str, data in self.data["number_stats"].items():
                number = int(num_str)
                stats[number] = {
                    'appearances': data['total_appearances'],
                    'last_seen': data['last_seen'],
                    'hot_streak': data['hot_streak'],
                    'cold_streak': data['cold_streak'],
                    'frequency': data['total_appearances'] / total_draws if total_draws > 0 else 0
                }
            
            return stats
            
        except Exception as e:
            logger.error(f"❌ Error getting number stats: {e}")
            return {}
    
    def get_total_draws(self):
        """Get total number of draws"""
        return len(self.data["draws"])
    
    def save_prediction(self, very_high: list, high: list, confidence: float):
        """Save prediction to database (optional)"""
        try:
            if "predictions" not in self.data:
                self.data["predictions"] = []
            
            prediction_record = {
                "time": datetime.now().isoformat(),
                "very_high": very_high,
                "high": high,
                "confidence": confidence
            }
            
            self.data["predictions"].append(prediction_record)
            return self.storage.save_data(self.data)
            
        except Exception as e:
            logger.error(f"❌ Error saving prediction: {e}")
            return False
    
    def get_gist_url(self):
        """Get URL to view the data"""
        return self.storage.get_gist_url()
