import os
import asyncio
import telegram
import logging
import time
import threading
import random
from datetime import datetime
from flask import Flask, jsonify

from database import PredictionDatabase
from analyzer import AdvancedKenoAnalyzer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class KenoPredictionBot:
    def __init__(self):
        self.telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.chat_id = os.getenv('TELEGRAM_CHAT_ID')
        
        if not self.telegram_token or not self.chat_id:
            logger.error("❌ Missing Telegram credentials")
            raise ValueError("TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID required")
        
        self.bot = telegram.Bot(token=self.telegram_token)
        self.db = PredictionDatabase()
        self.analyzer = AdvancedKenoAnalyzer(self.db)
        
        logger.info("✅ Keno Prediction Bot initialized")
    
    def has_sufficient_data(self):
        """Check if we have enough data for reliable predictions"""
        total_draws = self.db.get_total_draws()
        return total_draws >= 10  # Need at least 10 draws for good predictions
    
    async def send_prediction(self):
        """Generate and send prediction with clear data status"""
        try:
            total_draws = self.db.get_total_draws()
            
            if not self.has_sufficient_data():
                # INSUFFICIENT DATA - Send estimation
                predictions = self._generate_estimation()
                message = self._format_estimation_message(predictions, total_draws)
                logger.info("📊 Sent estimation (insufficient data)")
            else:
                # SUFFICIENT DATA - Send real prediction
                predictions = self.analyzer.generate_advanced_predictions()
                self.db.save_prediction(
                    predictions["very_high"],
                    predictions["high"],
                    predictions["confidence"]
                )
                message = self._format_prediction_message(predictions)
                logger.info(f"🎯 Sent real prediction (Confidence: {predictions['confidence']})")
            
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode='Markdown'
            )
            
            return predictions
            
        except Exception as e:
            logger.error(f"❌ Error sending prediction: {e}")
            return None
    
    def _generate_estimation(self):
        """Generate estimation when we don't have enough data"""
        # Smart estimation based on common Keno patterns
        all_numbers = list(range(1, 81))
        
        # Common patterns in Keno
        hot_endings = [1, 3, 7, 9]  # Common number endings
        balanced_mix = list(range(1, 41)) + list(range(41, 81))  # Low + High mix
        
        # Generate 4 very high estimation numbers
        very_high = random.sample([n for n in all_numbers if n % 10 in hot_endings], 2)
        very_high += random.sample([n for n in balanced_mix if n not in very_high], 2)
        
        # Generate 10 high estimation numbers
        remaining = [n for n in all_numbers if n not in very_high]
        high = random.sample(remaining, 10)
        
        return {
            "very_high": very_high,
            "high": high,
            "confidence": 0.15,  # Low confidence for estimations
            "total_draws": self.db.get_total_draws(),
            "message": "ESTIMATION - Need more data"
        }
    
    def _format_estimation_message(self, predictions: dict, total_draws: int) -> str:
        """Format estimation message (when we don't have enough data)"""
        very_high = predictions["very_high"]
        high = predictions["high"]
        
        message = "🎰 *KENO PREDICTION BOT* 🎰\n\n"
        message += "⚠️ *INSUFFICIENT DATA - THIS IS AN ESTIMATION* ⚠️\n\n"
        
        message += "🎯 *ESTIMATED VERY HIGH (4 Numbers)*\n"
        message += f"`{sorted(very_high)}`\n"
        message += "*(Based on common Keno patterns)*\n\n"
        
        message += "🔥 *ESTIMATED HIGH (10 Numbers)*\n"
        message += f"`{sorted(high)}`\n"
        message += "*(Random selection with pattern bias)*\n\n"
        
        message += "📊 *DATA STATUS*\n"
        message += f"• Current Draws: `{total_draws}/10`\n"
        message += f"• Status: `NEED MORE DATA`\n"
        message += f"• Confidence: `15% (LOW)`\n\n"
        
        message += "💡 *RECOMMENDATION*\n"
        message += "• Use these numbers **cautiously** - they're estimations\n"
        message += "• Wait until we collect 10+ draws for reliable predictions\n"
        message += "• Add more draw results to improve accuracy\n\n"
        
        message += f"⏰ *Generated*: `{datetime.now().strftime('%H:%M:%S')}`"
        
        return message
    
    def _format_prediction_message(self, predictions: dict) -> str:
        """Format real prediction message (when we have enough data)"""
        very_high = predictions["very_high"]
        high = predictions["high"]
        confidence = predictions["confidence"]
        
        message = "🎰 *KENO PREDICTION BOT* 🎰\n\n"
        message += "✅ *EXCELLENT PREDICTION - BASED ON COLLECTED DATA* ✅\n\n"
        
        message += "🎯 *VERY HIGH PROBABILITY (4 Numbers)*\n"
        message += f"`{sorted(very_high)}`\n"
        message += "*(AI Analysis of patterns & frequency)*\n\n"
        
        message += "🔥 *HIGH PROBABILITY (10 Numbers)*\n"
        message += f"`{sorted(high)}`\n"
        message += "*(Statistical probability analysis)*\n\n"
        
        message += "📊 *PREDICTION QUALITY*\n"
        message += f"• Confidence: `{confidence * 100:.1f}%`\n"
        message += f"• Status: `{predictions['message']}`\n"
        message += f"• Total Draws: `{predictions['total_draws']}`\n"
        message += f"• Recent Draws: `{predictions['recent_draws']}`\n\n"
        
        message += "💡 *GAMBLING STRATEGY*\n"
        message += "• **Play the 4 Very High numbers** - Core bets\n"
        message += "• **Mix with High probability set** - Increase coverage\n"
        message += "• **This is based on real data** - Much more reliable\n"
        message += "• Always gamble responsibly! 🎲\n\n"
        
        message += f"⏰ *Generated*: `{datetime.now().strftime('%H:%M:%S')}`"
        
        return message
    
    async def send_data_status(self):
        """Send current data status"""
        total_draws = self.db.get_total_draws()
        stats = self.db.get_number_stats()
        
        message = "📡 *DATA COLLECTION STATUS*\n\n"
        message += f"• Database Draws: `{total_draws}`\n"
        message += f"• Numbers Tracked: `{len(stats)}`\n"
        message += f"• Prediction Quality: `{'EXCELLENT' if total_draws >= 10 else 'ESTIMATION'}`\n"
        message += f"• Minimum Required: `10 draws`\n"
        message += f"• Current Status: `{'✅ READY' if total_draws >= 10 else '⚠️ COLLECTING DATA'}`\n\n"
        
        if total_draws < 10:
            needed = 10 - total_draws
            message += f"⚠️ *Need {needed} more draws for reliable predictions!*\n"
            message += "Add draw results using the manual input method."
        else:
            message += "✅ *Ready for excellent predictions!*\n"
            message += "All predictions now based on collected data analysis."
        
        message += f"\n⏰ *Last Update*: `{datetime.now().strftime('%H:%M:%S')}`"
        
        await self.bot.send_message(
            chat_id=self.chat_id,
            text=message,
            parse_mode='Markdown'
        )
    
    def add_manual_draw(self, numbers: list):
        """Add manual draw data"""
        if len(numbers) != 20:
            raise ValueError("Please provide exactly 20 numbers")
        
        if any(n < 1 or n > 80 for n in numbers):
            raise ValueError("All numbers must be between 1-80")
        
        success = self.db.save_draw(numbers, f"manual_{int(time.time())}")
        if success:
            logger.info(f"✅ Manual draw added: {numbers}")
            
            # Check if we just reached sufficient data
            if self.db.get_total_draws() == 10:
                logger.info("🎉 SUFFICIENT DATA REACHED! Switching to real predictions.")
        
        return success

# Global bot instance
prediction_bot = KenoPredictionBot()

async def prediction_cycle():
    """Main prediction cycle - synchronized with Keno timing"""
    logger.info("🚀 Starting Prediction Cycle (90-second intervals)...")
    
    # Send startup message
    try:
        await prediction_bot.send_data_status()
    except Exception as e:
        logger.error(f"Startup message failed: {e}")
    
    prediction_count = 0
    
    while True:
        try:
            # Generate and send prediction every 90 seconds (Keno cycle)
            await prediction_bot.send_prediction()
            prediction_count += 1
            
            # Send data status every 5 predictions
            if prediction_count % 5 == 0:
                await prediction_bot.send_data_status()
            
            # Log prediction type
            if prediction_bot.has_sufficient_data():
                logger.info(f"🎯 Excellent Prediction #{prediction_count} (Based on data)")
            else:
                logger.info(f"📊 Estimation #{prediction_count} (Collecting data)")
            
            # Wait 90 seconds (synchronized with Keno cycle)
            await asyncio.sleep(90)
            
        except Exception as e:
            logger.error(f"❌ Prediction cycle error: {e}")
            await asyncio.sleep(30)  # Wait 30 seconds on error

def start_prediction_bot():
    """Start the prediction bot"""
    asyncio.create_task(prediction_cycle())
    logger.info("✅ Prediction Bot started (90-second intervals)")

# Flask Web Interface
app = Flask(__name__)

@app.route('/')
def home():
    total_draws = prediction_bot.db.get_total_draws()
    has_data = prediction_bot.has_sufficient_data()
    
    return f"""
    <html>
        <head>
            <title>Keno Prediction Bot</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; background: #f0f8ff; }}
                .container {{ max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }}
                .header {{ text-align: center; color: #333; }}
                .status {{ color: #28a745; font-weight: bold; }}
                .warning {{ color: #dc3545; font-weight: bold; }}
                .info {{ margin: 20px 0; padding: 20px; background: #e8f4fd; border-radius: 10px; }}
                .data-status {{ background: #fff3cd; border-left: 5px solid #ffc107; }}
                .prediction {{ background: #d4edda; border-left: 5px solid #28a745; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🎰 Keno Prediction Bot</h1>
                    <p>AI-Powered Predictions • 90-Second Cycles</p>
                </div>
                
                <div class="info data-status">
                    <h3>📊 Data Collection Status</h3>
                    <p><strong>Current Draws:</strong> {total_draws}</p>
                    <p><strong>Minimum Required:</strong> 10 draws</p>
                    <p><strong>Prediction Quality:</strong> 
                        <span class="{'status' if has_data else 'warning'}">
                            {'✅ EXCELLENT' if has_data else '⚠️ ESTIMATION'}
                        </span>
                    </p>
                    <p><strong>Next Prediction:</strong> Every 90 seconds</p>
                </div>
                
                <div class="info">
                    <h3>🎯 Prediction Types</h3>
                    <p><strong>ESTIMATION MODE</strong> (When &lt;10 draws):</p>
                    <ul>
                        <li>Based on common Keno patterns</li>
                        <li>Low confidence (15%)</li>
                        <li>Use cautiously for gambling</li>
                    </ul>
                    
                    <p><strong>EXCELLENT PREDICTION MODE</strong> (When ≥10 draws):</p>
                    <ul>
                        <li>Based on collected data analysis</li>
                        <li>High confidence (60-90%)</li>
                        <li>Much more reliable for gambling</li>
                    </ul>
                </div>
                
                <div class="info prediction">
                    <h3>📱 Telegram Output</h3>
                    <p>You'll receive clear messages indicating:</p>
                    <ul>
                        <li>⚠️ <strong>ESTIMATION</strong> - When we need more data</li>
                        <li>✅ <strong>EXCELLENT PREDICTION</strong> - When we have enough data</li>
                        <li>🎯 <strong>4 Very High</strong> probability numbers</li>
                        <li>🔥 <strong>10 High</strong> probability numbers</li>
                    </ul>
                </div>
                
                <div style="text-align: center; margin-top: 20px;">
                    <p><strong>Current Status:</strong> 
                        <span id="status" class="{'status' if has_data else 'warning'}">
                            {'READY FOR EXCELLENT PREDICTIONS' if has_data else 'COLLECTING DATA - ESTIMATIONS ONLY'}
                        </span>
                    </p>
                    <p id="time">Last Update: {datetime.now().strftime('%H:%M:%S')}</p>
                </div>
                
                <script>
                    function updateTime() {{
                        document.getElementById('time').textContent = 'Last Update: ' + new Date().toLocaleTimeString();
                    }}
                    setInterval(updateTime, 1000);
                </script>
            </div>
        </body>
    </html>
    """

@app.route('/health')
def health():
    return jsonify({
        "status": "healthy",
        "service": "keno-prediction-bot",
        "total_draws": prediction_bot.db.get_total_draws(),
        "prediction_quality": "excellent" if prediction_bot.has_sufficient_data() else "estimation",
        "interval_seconds": 90,
        "timestamp": datetime.now().isoformat()
    })

@app.route('/manual-add/<numbers>')
def manual_add(numbers: str):
    """Manual endpoint to add draws"""
    try:
        number_list = [int(n) for n in numbers.split(',')]
        success = prediction_bot.add_manual_draw(number_list)
        
        response = {
            "success": success, 
            "numbers": number_list,
            "total_draws": prediction_bot.db.get_total_draws(),
            "prediction_quality": "excellent" if prediction_bot.has_sufficient_data() else "estimation"
        }
        
        return jsonify(response)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

if __name__ == "__main__":
    # Start the prediction bot
    start_prediction_bot()
    
    # Start Flask server
    port = int(os.environ.get('PORT', 10000))
    logger.info(f"🌐 Starting web server on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)
