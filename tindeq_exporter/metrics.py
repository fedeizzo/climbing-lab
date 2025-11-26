"""
Core metrics and calculations for Tindeq training data analysis
"""

from datetime import datetime, timedelta
from typing import Dict

import numpy as np
import pandas as pd


def calculate_training_frequency(sessions: pd.DataFrame, days: int = 7) -> Dict:
    """
    Calculate training frequency metrics

    Args:
        sessions: DataFrame of sessions
        days: Number of days to look back

    Returns:
        Dict with frequency metrics
    """
    if sessions.empty:
        return {
            "total_sessions": 0,
            "sessions_per_week": 0,
            "days_trained": 0,
            "training_rate": 0,
        }

    sessions = sessions.copy()
    sessions["date"] = pd.to_datetime(sessions["date"])

    cutoff_date = sessions["date"].max() - timedelta(days=days)
    recent = sessions[sessions["date"] >= cutoff_date]

    unique_days = recent["date"].dt.date.nunique()
    total_sessions = len(recent)

    return {
        "total_sessions": total_sessions,
        "sessions_per_week": (total_sessions / days) * 7,
        "days_trained": unique_days,
        "training_rate": (unique_days / days) * 100,  # percentage of days trained
    }


def calculate_streak(sessions: pd.DataFrame) -> Dict:
    """
    Calculate training streak (consecutive days with at least one session)

    Returns:
        Dict with current and longest streak
    """
    if sessions.empty:
        return {
            "current_streak": 0,
            "longest_streak": 0,
            "last_training_date": None,
        }

    sessions = sessions.copy()
    sessions["date"] = pd.to_datetime(sessions["date"])

    # Get unique training dates
    training_dates = sorted(sessions["date"].dt.date.unique())

    if not training_dates:
        return {
            "current_streak": 0,
            "longest_streak": 0,
            "last_training_date": None,
        }

    # Calculate current streak
    today = datetime.now().date()
    current_streak = 0

    # Check if training happened today or yesterday (to allow for current streak)
    last_date = training_dates[-1]
    days_since_last = (today - last_date).days

    if days_since_last <= 1:  # Today or yesterday
        current_streak = 1
        check_date = last_date - timedelta(days=1)

        for date in reversed(training_dates[:-1]):
            if date == check_date:
                current_streak += 1
                check_date -= timedelta(days=1)
            else:
                break

    # Calculate longest streak
    longest_streak = 1
    temp_streak = 1

    for i in range(1, len(training_dates)):
        if (training_dates[i] - training_dates[i - 1]).days == 1:
            temp_streak += 1
            longest_streak = max(longest_streak, temp_streak)
        else:
            temp_streak = 1

    return {
        "current_streak": current_streak,
        "longest_streak": longest_streak,
        "last_training_date": str(last_date),
    }


def calculate_morning_evening_split(sessions: pd.DataFrame) -> Dict:
    """
    Calculate distribution of morning vs evening sessions

    Returns:
        Dict with morning/evening counts and percentages
    """
    if sessions.empty:
        return {
            "morning_count": 0,
            "evening_count": 0,
            "morning_pct": 0,
            "evening_pct": 0,
        }

    sessions = sessions.copy()

    # Classify based on tag if available
    morning = sessions["tag"].str.contains("morning", case=False, na=False).sum()
    evening = sessions["tag"].str.contains("evening", case=False, na=False).sum()

    # If no tags, try to classify by time
    if morning == 0 and evening == 0:
        sessions["hour"] = pd.to_datetime(sessions["date"]).dt.hour
        morning = (sessions["hour"] < 12).sum()
        evening = (sessions["hour"] >= 12).sum()

    total = morning + evening

    return {
        "morning_count": morning,
        "evening_count": evening,
        "morning_pct": (morning / total * 100) if total > 0 else 0,
        "evening_pct": (evening / total * 100) if total > 0 else 0,
    }


def calculate_performance_trend(progress: pd.DataFrame, metric: str = "peak_weight") -> Dict:
    """
    Calculate trend in performance metric over time

    Args:
        progress: DataFrame with date, side, and performance metrics
        metric: Which metric to analyze (peak_weight, avg_weight, rfd2080)

    Returns:
        Dict with trend statistics
    """
    if progress.empty or metric not in progress.columns:
        return {
            "trend_direction": "unknown",
            "change_pct": 0,
            "slope": 0,
            "recent_avg": 0,
            "early_avg": 0,
        }

    progress = progress.copy()
    progress["date"] = pd.to_datetime(progress["date"])
    progress = progress.sort_values("date")

    # Group by date to get daily averages
    daily = progress.groupby("date")[metric].mean()

    if len(daily) < 2:
        return {
            "trend_direction": "insufficient_data",
            "change_pct": 0,
            "slope": 0,
            "recent_avg": daily.iloc[0] if len(daily) > 0 else 0,
            "early_avg": daily.iloc[0] if len(daily) > 0 else 0,
        }

    # Calculate linear regression slope
    x = np.arange(len(daily))
    y = daily.values
    slope = np.polyfit(x, y, 1)[0]

    # Compare first third vs last third
    split = len(daily) // 3
    early_avg = daily.iloc[:split].mean() if split > 0 else daily.iloc[0]
    recent_avg = daily.iloc[-split:].mean() if split > 0 else daily.iloc[-1]

    change_pct = ((recent_avg - early_avg) / early_avg * 100) if early_avg > 0 else 0

    # Determine trend direction
    if abs(change_pct) < 1:
        trend_direction = "stable"
    elif change_pct > 0:
        trend_direction = "improving"
    else:
        trend_direction = "declining"

    return {
        "trend_direction": trend_direction,
        "change_pct": round(change_pct, 2),
        "slope": round(slope, 4),
        "recent_avg": round(recent_avg, 2),
        "early_avg": round(early_avg, 2),
    }


def calculate_left_right_balance(progress: pd.DataFrame, metric: str = "peak_weight") -> Dict:
    """
    Calculate left/right asymmetry

    Returns:
        Dict with balance metrics
    """
    if progress.empty or "side" not in progress.columns:
        return {
            "left_avg": 0,
            "right_avg": 0,
            "asymmetry_pct": 0,
            "stronger_side": "unknown",
        }

    left_data = progress[progress["side"] == "left"][metric]
    right_data = progress[progress["side"] == "right"][metric]

    if left_data.empty or right_data.empty:
        return {
            "left_avg": left_data.mean() if not left_data.empty else 0,
            "right_avg": right_data.mean() if not right_data.empty else 0,
            "asymmetry_pct": 0,
            "stronger_side": "unknown",
        }

    left_avg = left_data.mean()
    right_avg = right_data.mean()

    asymmetry_pct = abs(left_avg - right_avg) / max(left_avg, right_avg) * 100
    stronger_side = "left" if left_avg > right_avg else "right"

    return {
        "left_avg": round(left_avg, 2),
        "right_avg": round(right_avg, 2),
        "asymmetry_pct": round(asymmetry_pct, 2),
        "stronger_side": stronger_side,
    }


def calculate_intra_session_fatigue(set_stats: pd.DataFrame, metric: str = "peak_weight") -> Dict:
    """
    Analyze fatigue within a session by comparing early vs late sets

    Args:
        set_stats: DataFrame with set-level statistics
        metric: Which metric to analyze

    Returns:
        Dict with fatigue metrics
    """
    if set_stats.empty or "set_num" not in set_stats.columns:
        return {
            "first_set_avg": 0,
            "last_set_avg": 0,
            "fatigue_pct": 0,
            "fatigue_direction": "unknown",
        }

    set_stats = set_stats.sort_values("set_num")

    # Get first and last sets
    first_sets = set_stats[set_stats["set_num"] == set_stats["set_num"].min()]
    last_sets = set_stats[set_stats["set_num"] == set_stats["set_num"].max()]

    first_avg = first_sets[metric].mean()
    last_avg = last_sets[metric].mean()

    fatigue_pct = ((last_avg - first_avg) / first_avg * 100) if first_avg > 0 else 0

    if fatigue_pct < -5:
        fatigue_direction = "significant_decline"
    elif fatigue_pct < -2:
        fatigue_direction = "mild_decline"
    elif fatigue_pct < 2:
        fatigue_direction = "stable"
    else:
        fatigue_direction = "improving"  # Getting stronger during session

    return {
        "first_set_avg": round(first_avg, 2),
        "last_set_avg": round(last_avg, 2),
        "fatigue_pct": round(fatigue_pct, 2),
        "fatigue_direction": fatigue_direction,
    }


def calculate_rep_consistency(rep_stats: pd.DataFrame, metric: str = "peak_weight") -> Dict:
    """
    Calculate coefficient of variation for reps within sets

    Lower CV = more consistent performance

    Returns:
        Dict with consistency metrics
    """
    if rep_stats.empty or metric not in rep_stats.columns:
        return {"mean": 0, "std": 0, "cv": 0, "consistency_rating": "unknown"}

    mean_val = rep_stats[metric].mean()
    std_val = rep_stats[metric].std()
    cv = (std_val / mean_val * 100) if mean_val > 0 else 0

    # Rate consistency
    if cv < 5:
        rating = "excellent"
    elif cv < 10:
        rating = "good"
    elif cv < 15:
        rating = "fair"
    else:
        rating = "variable"

    return {
        "mean": round(mean_val, 2),
        "std": round(std_val, 2),
        "cv": round(cv, 2),
        "consistency_rating": rating,
    }


def calculate_recovery_quality(
    morning_sessions: pd.DataFrame,
    evening_sessions: pd.DataFrame,
    exercise: str,
    metric: str = "peak_weight",
) -> Dict:
    """
    Compare evening performance to next morning to assess recovery

    Args:
        morning_sessions: Morning session data with progress
        evening_sessions: Evening session data with progress
        exercise: Exercise name to analyze
        metric: Which metric to compare

    Returns:
        Dict with recovery quality metrics
    """
    if morning_sessions.empty or evening_sessions.empty:
        return {
            "avg_recovery_pct": 0,
            "recovery_rating": "unknown",
            "morning_avg": 0,
            "evening_avg": 0,
        }

    morning_avg = morning_sessions[metric].mean()
    evening_avg = evening_sessions[metric].mean()

    # Typically morning should be close to or better than previous evening
    recovery_pct = ((morning_avg - evening_avg) / evening_avg * 100) if evening_avg > 0 else 0

    if recovery_pct > 2:
        rating = "excellent"  # Morning stronger than evening
    elif recovery_pct > -2:
        rating = "good"  # About the same
    elif recovery_pct > -5:
        rating = "fair"  # Slight decline
    else:
        rating = "poor"  # Significant decline

    return {
        "avg_recovery_pct": round(recovery_pct, 2),
        "recovery_rating": rating,
        "morning_avg": round(morning_avg, 2),
        "evening_avg": round(evening_avg, 2),
    }


def calculate_volume_metrics(progress: pd.DataFrame) -> Dict:
    """
    Calculate total volume metrics across sessions

    Returns:
        Dict with volume statistics
    """
    if progress.empty:
        return {
            "total_sets": 0,
            "avg_sets_per_session": 0,
            "total_reps": 0,
            "avg_weight_volume": 0,
        }

    # Group by session
    sessions = progress.groupby(["date", "session_id"]).agg({"set_num": "nunique", "avg_weight": "mean"}).reset_index()

    total_sets = progress["set_num"].nunique() * len(progress["date"].unique())
    avg_sets = sessions["set_num"].mean()

    # Estimate total reps (assuming 6 reps per set typically)
    total_reps = total_sets * 6  # This is an estimate

    return {
        "total_sets": total_sets,
        "avg_sets_per_session": round(avg_sets, 1),
        "total_reps": total_reps,
        "avg_weight_volume": round(progress["avg_weight"].mean(), 2),
    }


def calculate_rolling_average(progress: pd.DataFrame, metric: str = "peak_weight", window: int = 7) -> pd.DataFrame:
    """
    Calculate rolling average for a metric

    Args:
        progress: DataFrame with date and metric columns
        metric: Metric to calculate rolling average for
        window: Window size in days

    Returns:
        DataFrame with date, value, and rolling_avg columns
    """
    if progress.empty:
        return pd.DataFrame()

    progress = progress.copy()
    progress["date"] = pd.to_datetime(progress["date"])

    # Get daily averages
    daily = progress.groupby("date")[metric].mean().reset_index()
    daily = daily.sort_values("date")

    # Calculate rolling average
    daily["rolling_avg"] = daily[metric].rolling(window=window, min_periods=1).mean()

    return daily
