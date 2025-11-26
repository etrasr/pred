import math
import random
import logging
from collections import Counter, defaultdict
from typing import List, Dict, Tuple

logger = logging.getLogger(__name__)

class AdvancedKenoAnalyzer:
    def __init__(self, database):
        self.db = database
    
    def calculate_advanced_probabilities(self, draws: List[Dict]) -> Dict[int, float]:
        """Calculate advanced probabilities using multiple factors"""
        if len(draws) < 3:
            return self._get_default_probabilities()
        
        # Factor 1: Basic frequency
        freq_scores = self._calculate_frequency_scores(draws)
        
        # Factor 2: Recency weighting
        recency_scores = self._calculate_recency_scores(draws)
        
        # Factor 3: Hot/Cold analysis
        hot_cold_scores = self._calculate_hot_cold_scores(draws)
        
        # Factor 4: Pattern analysis
        pattern_scores = self._calculate_pattern_scores(draws)
        
        # Factor 5: Streak analysis
        streak_scores = self._calculate_streak_scores()
        
        # Combine all factors
        combined_scores = {}
        for number in range(1, 81):
            score = (
                freq_scores.get(number, 0) * 0.25 +
                recency_scores.get(number, 0) * 0.30 +
                hot_cold_scores.get(number, 0) * 0.20 +
                pattern_scores.get(number, 0) * 0.15 +
                streak_scores.get(number, 0) * 0.10
            )
            combined_scores[number] = max(score, 0.001)
        
        # Normalize
        total = sum(combined_scores.values())
        return {k: v/total for k, v in combined_scores.items()}
    
    def _calculate_frequency_scores(self, draws: List[Dict]) -> Dict[int, float]:
        """Calculate frequency-based scores"""
        number_counts = Counter()
        total_draws = len(draws)
        
        for draw in draws:
            number_counts.update(draw['numbers'])
        
        scores = {}
        for number in range(1, 81):
            count = number_counts.get(number, 0)
            scores[number] = count / total_draws if total_draws > 0 else 0.01
        
        return scores
    
    def _calculate_recency_scores(self, draws: List[Dict]) -> Dict[int, float]:
        """Calculate recency-weighted scores"""
        if not draws:
            return {}
        
        scores = {}
        total_draws = len(draws)
        
        for i, draw in enumerate(draws):
            weight = 1.0 + (total_draws - i) * 0.1
            for number in draw['numbers']:
                scores[number] = scores.get(number, 0) + weight
        
        # Normalize
        max_score = max(scores.values()) if scores else 1
        return {k: v/max_score for k, v in scores.items()}
    
    def _calculate_hot_cold_scores(self, draws: List[Dict]) -> Dict[int, float]:
        """Calculate hot/cold number scores"""
        if len(draws) < 10:
            return {}
        
        recent_count = max(5, len(draws) // 3)
        recent_draws = draws[:recent_count]
        older_draws = draws[recent_count:]
        
        recent_numbers = set()
        for draw in recent_draws:
            recent_numbers.update(draw['numbers'])
        
        older_numbers = set()
        for draw in older_draws:
            older_numbers.update(draw['numbers'])
        
        scores = {}
        for number in range(1, 81):
            if number in recent_numbers and number not in older_numbers:
                scores[number] = 1.0
            elif number not in recent_numbers and number in older_numbers:
                scores[number] = 0.3
            elif number in recent_numbers:
                scores[number] = 0.7
            else:
                scores[number] = 0.1
        
        return scores
    
    def _calculate_pattern_scores(self, draws: List[Dict]) -> Dict[int, float]:
        """Calculate pattern-based scores"""
        if len(draws) < 3:
            return {}
        
        last_draw = draws[0]['numbers']
        patterns = self._analyze_draw_patterns(last_draw)
        
        scores = {}
        for number in range(1, 81):
            score = 0.0
            
            if number % 10 in patterns.get('endings', []):
                score += 0.3
            
            if (number - 1) // 10 in patterns.get('decades', []):
                score += 0.3
            
            if number <= 40 and patterns.get('low_high_balance', 0) > 0.5:
                score += 0.2
            elif number > 40 and patterns.get('low_high_balance', 0) < 0.5:
                score += 0.2
            
            if number % 2 == 0 and patterns.get('even_odd_balance', 0) > 0.5:
                score += 0.2
            elif number % 2 == 1 and patterns.get('even_odd_balance', 0) < 0.5:
                score += 0.2
            
            scores[number] = min(score, 1.0)
        
        return scores
    
    def _calculate_streak_scores(self) -> Dict[int, float]:
        """Calculate scores based on hot/cold streaks"""
        stats = self.db.get_number_stats()
        scores = {}
        
        for number in range(1, 81):
            number_stats = stats.get(number, {})
            hot_streak = number_stats.get('hot_streak', 0)
            cold_streak = number_stats.get('cold_streak', 0)
            
            if hot_streak >= 3:
                scores[number] = 0.8
            elif hot_streak >= 2:
                scores[number] = 0.6
            elif cold_streak >= 5:
                scores[number] = 0.9
            elif cold_streak >= 3:
                scores[number] = 0.7
            else:
                scores[number] = 0.5
        
        return scores
    
    def _analyze_draw_patterns(self, numbers: List[int]) -> Dict:
        """Analyze patterns in the most recent draw"""
        patterns = {
            'endings': [],
            'decades': [],
            'low_high_balance': 0,
            'even_odd_balance': 0
        }
        
        # Analyze number endings
        endings = [n % 10 for n in numbers]
        patterns['endings'] = list(set(endings))
        
        # Analyze decades
        decades = [(n - 1) // 10 for n in numbers]
        patterns['decades'] = list(set(decades))
        
        # Low/High balance (1-40 vs 41-80)
        low_count = sum(1 for n in numbers if n <= 40)
        patterns['low_high_balance'] = low_count / len(numbers)
        
        # Even/Odd balance
        even_count = sum(1 for n in numbers if n % 2 == 0)
        patterns['even_odd_balance'] = even_count / len(numbers)
        
        return patterns
    
    def _get_default_probabilities(self) -> Dict[int, float]:
        """Return default probabilities when insufficient data"""
        return {i: 1/80 for i in range(1, 81)}
    
    def generate_advanced_predictions(self) -> Dict[str, any]:
        """Generate advanced predictions with confidence scores"""
        recent_draws = self.db.get_recent_draws(hours=72, limit=100)
        total_draws = self.db.get_total_draws()
        
        if total_draws < 5:
            return {
                "very_high": random.sample(range(1, 81), 4),
                "high": random.sample(range(1, 81), 10),
                "confidence": 0.1,
                "message": "⚠️ Low confidence - Need more data"
            }
        
        # Calculate probabilities
        probabilities = self.calculate_advanced_probabilities(recent_draws)
        
        # Generate very high probability numbers (top 4)
        very_high = sorted(probabilities.items(), key=lambda x: x[1], reverse=True)[:4]
        very_high_numbers = [num for num, prob in very_high]
        
        # Generate high probability numbers (next 10, excluding very high)
        high_candidates = sorted(probabilities.items(), key=lambda x: x[1], reverse=True)[4:20]
        high_numbers = [num for num, prob in high_candidates[:10]]
        
        # Calculate confidence score
        confidence = self._calculate_confidence(recent_draws, probabilities)
        
        return {
            "very_high": very_high_numbers,
            "high": high_numbers,
            "confidence": round(confidence, 3),
            "total_draws": total_draws,
            "recent_draws": len(recent_draws),
            "message": self._get_confidence_message(confidence)
        }
    
    def _calculate_confidence(self, draws: List[Dict], probabilities: Dict[int, float]) -> float:
        """Calculate prediction confidence score"""
        if len(draws) < 10:
            return 0.3
        
        # Base confidence on data quantity
        data_confidence = min(len(draws) / 50, 1.0)
        
        # Confidence based on probability distribution
        top_probs = sorted(probabilities.values(), reverse=True)[:10]
        prob_confidence = sum(top_probs) / 1.0
        
        # Pattern consistency
        pattern_confidence = self._calculate_pattern_consistency(draws)
        
        # Combine confidence factors
        final_confidence = (
            data_confidence * 0.4 +
            prob_confidence * 0.4 +
            pattern_confidence * 0.2
        )
        
        return min(final_confidence, 0.95)
    
    def _calculate_pattern_consistency(self, draws: List[Dict]) -> float:
        """Calculate how consistent patterns are in recent draws"""
        if len(draws) < 5:
            return 0.5
        
        pattern_changes = 0
        total_comparisons = 0
        
        for i in range(min(5, len(draws) - 1)):
            current_patterns = self._analyze_draw_patterns(draws[i]['numbers'])
            next_patterns = self._analyze_draw_patterns(draws[i + 1]['numbers'])
            
            if set(current_patterns['endings']) != set(next_patterns['endings']):
                pattern_changes += 1
            total_comparisons += 1
        
        consistency = 1.0 - (pattern_changes / total_comparisons if total_comparisons > 0 else 0)
        return consistency
    
    def _get_confidence_message(self, confidence: float) -> str:
        """Get human-readable confidence message"""
        if confidence >= 0.8:
            return "🎯 HIGH CONFIDENCE"
        elif confidence >= 0.6:
            return "✅ GOOD CONFIDENCE"
        elif confidence >= 0.4:
            return "⚠️ MODERATE CONFIDENCE"
        else:
            return "🔻 LOW CONFIDENCE"
