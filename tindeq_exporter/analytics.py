"""
High-level analytics functions for Tindeq training data
"""

import pandas as pd
from typing import Dict, Optional
from datetime import datetime, timedelta

from .storage import TindeqStorage
from . import metrics


class TindeqAnalytics:
    """High-level analytics for Tindeq training data"""

    def __init__(self, storage: TindeqStorage):
        self.storage = storage

    def analyze_consistency(self, days: int = 30) -> Dict:
        """
        Analyze training consistency over the specified period

        Args:
            days: Number of days to analyze

        Returns:
            Dict with consistency metrics
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        sessions = self.storage.list_sessions(
            start_date=start_date.strftime('%Y-%m-%d'),
            end_date=end_date.strftime('%Y-%m-%d')
        )

        # All sessions for streak calculation
        all_sessions = self.storage.list_sessions()

        frequency = metrics.calculate_training_frequency(sessions, days)
        streak = metrics.calculate_streak(all_sessions)
        split = metrics.calculate_morning_evening_split(sessions)

        return {
            'period_days': days,
            'frequency': frequency,
            'streak': streak,
            'morning_evening_split': split
        }

    def analyze_performance(self,
                           exercise: str,
                           metric: str = 'peak_weight',
                           days: Optional[int] = None) -> Dict:
        """
        Analyze performance trends for an exercise

        Args:
            exercise: Exercise name
            metric: Metric to analyze (peak_weight, avg_weight, rfd2080)
            days: Number of days to look back (None = all time)

        Returns:
            Dict with performance analysis
        """
        start_date = None
        if days:
            start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

        progress = self.storage.get_exercise_progress(exercise, start_date=start_date)

        if progress.empty:
            return {'error': f'No data found for exercise: {exercise}'}

        trend = metrics.calculate_performance_trend(progress, metric)
        balance = metrics.calculate_left_right_balance(progress, metric)
        rolling = metrics.calculate_rolling_average(progress, metric, window=7)

        return {
            'exercise': exercise,
            'metric': metric,
            'trend': trend,
            'left_right_balance': balance,
            'rolling_7day': rolling.tail(10).to_dict('records') if not rolling.empty else []
        }

    def analyze_session_fatigue(self, session_id: str, exercise: str) -> Dict:
        """
        Analyze fatigue patterns within a specific session

        Args:
            session_id: Session ID
            exercise: Exercise name

        Returns:
            Dict with fatigue analysis
        """
        try:
            rep_stats, set_stats = self.storage.get_exercise_stats(session_id, exercise)

            fatigue_peak = metrics.calculate_intra_session_fatigue(set_stats, 'peak_weight')
            fatigue_avg = metrics.calculate_intra_session_fatigue(set_stats, 'avg_weight')
            consistency = metrics.calculate_rep_consistency(rep_stats, 'peak_weight')

            return {
                'session_id': session_id,
                'exercise': exercise,
                'fatigue_peak_weight': fatigue_peak,
                'fatigue_avg_weight': fatigue_avg,
                'rep_consistency': consistency
            }

        except Exception as e:
            return {'error': str(e)}

    def analyze_recovery(self, exercise: str, days: int = 30) -> Dict:
        """
        Analyze recovery quality by comparing morning vs evening performance

        Args:
            exercise: Exercise name
            days: Number of days to look back

        Returns:
            Dict with recovery analysis
        """
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        progress = self.storage.get_exercise_progress(exercise, start_date=start_date)

        if progress.empty:
            return {'error': f'No data found for exercise: {exercise}'}

        # Split by morning/evening based on tag
        morning = progress[progress['tag'].str.contains('morning', case=False, na=False)]
        evening = progress[progress['tag'].str.contains('evening', case=False, na=False)]

        if morning.empty or evening.empty:
            return {
                'error': 'Insufficient morning/evening data',
                'morning_sessions': len(morning),
                'evening_sessions': len(evening)
            }

        recovery = metrics.calculate_recovery_quality(morning, evening, exercise, 'peak_weight')

        # Also analyze time-of-day performance differences
        morning_avg = morning.groupby('side')['peak_weight'].mean()
        evening_avg = evening.groupby('side')['peak_weight'].mean()

        return {
            'exercise': exercise,
            'period_days': days,
            'recovery_quality': recovery,
            'morning_avg_by_side': morning_avg.to_dict(),
            'evening_avg_by_side': evening_avg.to_dict(),
            'preferred_time': 'morning' if recovery['morning_avg'] > recovery['evening_avg'] else 'evening'
        }

    def generate_weekly_report(self, weeks: int = 4) -> Dict:
        """
        Generate a weekly summary report

        Args:
            weeks: Number of weeks to include

        Returns:
            Dict with weekly summary data
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(weeks=weeks*7)

        sessions = self.storage.list_sessions(
            start_date=start_date.strftime('%Y-%m-%d'),
            end_date=end_date.strftime('%Y-%m-%d')
        )

        if sessions.empty:
            return {'error': 'No sessions found in this period'}

        sessions['date'] = pd.to_datetime(sessions['date'])
        sessions['week'] = sessions['date'].dt.isocalendar().week
        sessions['year'] = sessions['date'].dt.year

        # Weekly aggregation
        weekly = sessions.groupby(['year', 'week']).agg({
            'session_id': 'count',
            'date': ['min', 'max']
        }).reset_index()

        weekly.columns = ['year', 'week', 'session_count', 'week_start', 'week_end']

        exercises = self.storage.get_all_exercises()
        exercise_progress = {}

        # Get progress for each exercise
        for exercise in exercises:
            progress = self.storage.get_exercise_progress(
                exercise,
                start_date=start_date.strftime('%Y-%m-%d')
            )

            if not progress.empty:
                weekly_avg = progress.groupby(
                    pd.to_datetime(progress['date']).dt.to_period('W')
                )['peak_weight'].mean()

                exercise_progress[exercise] = weekly_avg.to_dict()

        return {
            'period': f'{weeks} weeks',
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d'),
            'weekly_sessions': weekly.to_dict('records'),
            'exercise_progress': exercise_progress,
            'total_sessions': len(sessions),
            'avg_sessions_per_week': len(sessions) / weeks
        }

    def generate_monthly_report(self, months: int = 3) -> Dict:
        """
        Generate a monthly summary report

        Args:
            months: Number of months to include

        Returns:
            Dict with monthly summary data
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=months*30)

        sessions = self.storage.list_sessions(
            start_date=start_date.strftime('%Y-%m-%d'),
            end_date=end_date.strftime('%Y-%m-%d')
        )

        if sessions.empty:
            return {'error': 'No sessions found in this period'}

        sessions['date'] = pd.to_datetime(sessions['date'])
        sessions['month'] = sessions['date'].dt.to_period('M')

        # Monthly aggregation
        monthly = sessions.groupby('month').agg({
            'session_id': 'count',
            'date': ['min', 'max']
        }).reset_index()

        monthly.columns = ['month', 'session_count', 'month_start', 'month_end']
        monthly['month'] = monthly['month'].astype(str)

        exercises = self.storage.get_all_exercises()
        exercise_trends = {}

        # Get trends for each exercise
        for exercise in exercises:
            progress = self.storage.get_exercise_progress(
                exercise,
                start_date=start_date.strftime('%Y-%m-%d')
            )

            if not progress.empty:
                trend = metrics.calculate_performance_trend(progress, 'peak_weight')
                exercise_trends[exercise] = trend

        # Overall consistency
        consistency = self.analyze_consistency(days=months*30)

        return {
            'period': f'{months} months',
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d'),
            'monthly_sessions': monthly.to_dict('records'),
            'exercise_trends': exercise_trends,
            'consistency': consistency,
            'total_sessions': len(sessions)
        }

    def compare_exercises(self, days: int = 30) -> Dict:
        """
        Compare performance across all exercises

        Args:
            days: Number of days to look back

        Returns:
            Dict with exercise comparisons
        """
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        exercises = self.storage.get_all_exercises()

        comparisons = []

        for exercise in exercises:
            progress = self.storage.get_exercise_progress(exercise, start_date=start_date)

            if not progress.empty:
                trend = metrics.calculate_performance_trend(progress, 'peak_weight')
                balance = metrics.calculate_left_right_balance(progress, 'peak_weight')

                comparisons.append({
                    'exercise': exercise,
                    'avg_peak_weight': round(progress['peak_weight'].mean(), 2),
                    'trend': trend['trend_direction'],
                    'change_pct': trend['change_pct'],
                    'asymmetry_pct': balance['asymmetry_pct'],
                    'sessions': progress.groupby('date').ngroups
                })

        # Sort by performance
        comparisons.sort(key=lambda x: x['avg_peak_weight'], reverse=True)

        return {
            'period_days': days,
            'exercises': comparisons,
            'strongest_exercise': comparisons[0]['exercise'] if comparisons else None,
            'most_improved': max(comparisons, key=lambda x: x['change_pct'])['exercise'] if comparisons else None
        }

    def identify_weak_points(self, days: int = 30) -> Dict:
        """
        Identify exercises that need more focus

        Args:
            days: Number of days to look back

        Returns:
            Dict with weak points analysis
        """
        comparison = self.compare_exercises(days)

        if not comparison['exercises']:
            return {'error': 'No exercise data available'}

        exercises = comparison['exercises']

        # Identify weak points
        declining = [e for e in exercises if e['trend'] == 'declining']
        high_asymmetry = [e for e in exercises if e['asymmetry_pct'] > 10]
        weakest = exercises[-1] if exercises else None

        recommendations = []

        if declining:
            recommendations.append(f"Focus on: {', '.join(e['exercise'] for e in declining)} (declining performance)")

        if high_asymmetry:
            recommendations.append(f"Address imbalance in: {', '.join(e['exercise'] for e in high_asymmetry)}")

        if weakest:
            recommendations.append(f"Strengthen: {weakest['exercise']} (lowest absolute strength)")

        return {
            'period_days': days,
            'declining_exercises': declining,
            'high_asymmetry_exercises': high_asymmetry,
            'weakest_exercise': weakest,
            'recommendations': recommendations
        }
