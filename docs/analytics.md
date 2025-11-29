# Tindeq Analytics Guide

Complete guide to analyzing your Tindeq training data.

## Quick Reference

```bash
# Consistency Analysis
tindeq analyze consistency --days 30

# Performance Trends
tindeq analyze performance --exercise "4_finger" --days 30

# Compare All Exercises
tindeq analyze compare --days 30

# Recovery Quality
tindeq analyze recovery --exercise "4_finger" --days 30

# Identify Weak Points
tindeq analyze weakpoints --days 30

# Session Fatigue
tindeq analyze fatigue --session-id <id> --exercise "4_finger"

# Weekly Report
tindeq report weekly --weeks 4

# Monthly Report
tindeq report monthly --months 3
```

## Metrics Explained

### 1. Consistency Metrics

**What it measures:**
- Training frequency and adherence
- Streaks and training patterns
- Morning vs evening distribution

**Use case:**
Track if you're maintaining your twice-daily training routine.

**Command:**
```bash
tindeq analyze consistency --days 30
```

**Output:**
- Total sessions in period
- Sessions per week
- Days trained (unique days with at least one session)
- Training rate (% of days with training)
- Current and longest streak
- Morning vs evening session split

**What to look for:**
- Aim for ~14 sessions per week (2x per day × 7 days)
- Training rate should be close to 100% for daily training
- Balanced morning/evening split

---

### 2. Performance Trends

**What it measures:**
- How your strength is changing over time
- Direction and magnitude of improvement
- Left/right asymmetry

**Use case:**
Track if you're getting stronger in specific exercises.

**Command:**
```bash
tindeq analyze performance --exercise "4_finger" --days 30
tindeq analyze performance --exercise "4_finger" --metric avg_weight --days 60
```

**Metrics available:**
- `peak_weight` - Maximum force in a rep (strength)
- `avg_weight` - Average force during work period (endurance)
- `rfd2080` - Rate of force development (explosiveness)

**Output:**
- Trend direction: improving, declining, or stable
- Percentage change (recent vs early in period)
- Recent vs early averages
- Left/right balance and asymmetry percentage

**What to look for:**
- Consistent "improving" trend
- Asymmetry < 10% (ideally < 5%)
- Steady increase in peak_weight over weeks/months

---

### 3. Exercise Comparison

**What it measures:**
- Relative strength across all exercises
- Which exercises are improving/declining
- Asymmetry patterns

**Use case:**
Identify your strongest and weakest grip types.

**Command:**
```bash
tindeq analyze compare --days 30
```

**Output:**
- All exercises ranked by average peak weight
- Trend and change % for each
- Asymmetry for each
- Strongest exercise
- Most improved exercise

**What to look for:**
- Consistent trends across similar grip types
- Identify which grips need more focus
- Monitor asymmetry across all exercises

---

### 4. Recovery Quality

**What it measures:**
- How well you recover between evening and next morning
- Morning vs evening performance patterns

**Use case:**
Determine if you're recovering properly between sessions and identify your optimal training time.

**Command:**
```bash
tindeq analyze recovery --exercise "4_finger" --days 30
```

**Output:**
- Recovery rating: excellent, good, fair, or poor
- Morning vs evening average strength
- Recovery percentage
- Preferred time based on when you're stronger

**What to look for:**
- "Excellent" or "good" recovery (morning ≥ previous evening)
- If recovery is "poor", you may need more rest
- Some people are naturally stronger in morning or evening

---

### 5. Intra-Session Fatigue

**What it measures:**
- Strength decline within a single session
- First set vs last set performance
- Rep-to-rep consistency

**Use case:**
Understand how fatigue accumulates during your workout.

**Command:**
```bash
tindeq analyze fatigue --session-id <session_id> --exercise "4_finger"
```

**Output:**
- First set vs last set averages
- Fatigue percentage (negative = strength declining)
- Fatigue direction: significant_decline, mild_decline, stable, or improving
- Coefficient of variation (CV) for consistency

**What to look for:**
- Mild decline (-2% to -5%) is normal for endurance work
- Significant decline (>-5%) may indicate overtraining
- "Improving" during session is unusual but can happen with proper warm-up
- CV < 5% = excellent consistency

---

### 6. Weak Points Identification

**What it measures:**
- Exercises showing declining performance
- High left/right asymmetries
- Overall weakest areas

**Use case:**
Get actionable recommendations on what to focus on.

**Command:**
```bash
tindeq analyze weakpoints --days 30
```

**Output:**
- List of declining exercises
- Exercises with high asymmetry (>10%)
- Weakest exercise by absolute strength
- Specific recommendations

**What to look for:**
- Focus training on declining exercises
- Address asymmetries early
- Strengthen weak grips

---

### 7. Weekly Reports

**What it measures:**
- Week-by-week session counts
- Exercise progress week over week

**Use case:**
Get a high-level overview of recent training.

**Command:**
```bash
tindeq report weekly --weeks 4
tindeq report weekly --weeks 4 --json > report.json
```

**Output:**
- Total sessions in period
- Average sessions per week
- Breakdown by week
- Exercise progress trends

**What to look for:**
- Consistent session count each week
- Steady progress across weeks

---

### 8. Monthly Reports

**What it measures:**
- Month-by-month training summary
- Long-term trends and consistency
- Overall progress across all exercises

**Use case:**
Track long-term progress and adherence.

**Command:**
```bash
tindeq report monthly --months 3
tindeq report monthly --months 6 --json > report.json
```

**Output:**
- Sessions per month
- Current streak and training rate
- Exercise trends for entire period
- Consistency metrics

**What to look for:**
- Increasing or maintaining strength over months
- Consistent training rate (>80%)
- Balanced improvement across exercises

---

## Recommended Analysis Workflow

### Daily Check (30 seconds)
```bash
# Quick consistency check
tindeq analyze consistency --days 7
```

### Weekly Review (2 minutes)
```bash
# Check progress on main exercises
tindeq analyze performance --exercise "4_finger" --days 7
tindeq analyze performance --exercise "3_finger_drag" --days 7

# Compare all exercises
tindeq analyze compare --days 7

# Weekly summary
tindeq report weekly --weeks 1
```

### Monthly Review (5 minutes)
```bash
# Long-term trends
tindeq analyze performance --exercise "4_finger" --days 30
tindeq analyze performance --exercise "3_finger_drag" --days 30

# Recovery quality
tindeq analyze recovery --exercise "4_finger" --days 30

# Identify issues
tindeq analyze weakpoints --days 30

# Monthly summary
tindeq report monthly --months 1
```

### Quarterly Review (10 minutes)
```bash
# 3-month trends for all exercises
tindeq report monthly --months 3

# Compare long-term progress
tindeq analyze compare --days 90

# Check all exercises
for exercise in $(tindeq exercises | tail -n +3 | sed 's/^  - //'); do
    echo "=== $exercise ==="
    tindeq analyze performance --exercise "$exercise" --days 90
done
```

## Interpreting Your Data

### What is "Good" Progress?

For light, twice-daily training:

- **Strength gains**: 1-3% per month is excellent
- **Consistency**: >90% training rate (missing <1 day per week)
- **Recovery**: "Good" or better recovery quality
- **Asymmetry**: <5% is ideal, <10% is acceptable
- **Fatigue**: Mild decline (-2% to -5%) within session is normal

### Red Flags

⚠️ Pay attention to:

- Declining performance across multiple exercises
- Poor recovery quality (morning much weaker than evening)
- Significant fatigue (>-10%) within sessions
- Asymmetry increasing over time
- Consistency <80%

These may indicate:
- Overtraining
- Insufficient recovery
- Technique issues
- Injury risk

### Green Flags

✅ You're on track when:

- Consistent "improving" or "stable" trends
- Good recovery between sessions
- Asymmetry stable or decreasing
- Consistency >90%
- Mild, manageable fatigue during sessions

## Python API

Use analytics programmatically:

```python
from tindeq_exporter import TindeqStorage, TindeqAnalytics

storage = TindeqStorage("tindeq_data")
analytics = TindeqAnalytics(storage)

# Get consistency metrics
consistency = analytics.analyze_consistency(days=30)
print(f"Current streak: {consistency['streak']['current_streak']} days")

# Get performance analysis
performance = analytics.analyze_performance("4_finger", days=30)
print(f"Trend: {performance['trend']['trend_direction']}")
print(f"Change: {performance['trend']['change_pct']}%")

# Compare exercises
comparison = analytics.compare_exercises(days=30)
for ex in comparison['exercises']:
    print(f"{ex['exercise']}: {ex['avg_peak_weight']} kg ({ex['trend']})")

# Get weekly report
report = analytics.generate_weekly_report(weeks=4)
print(f"Total sessions: {report['total_sessions']}")
```

## Tips

1. **Track consistently** - Import data weekly to maintain accurate history

2. **Focus on trends** - Day-to-day variation is normal, look at weekly/monthly trends

3. **Balance training** - Use "compare" to ensure you're not neglecting certain grip types

4. **Monitor recovery** - If recovery quality drops, consider an extra rest day

5. **Address asymmetries early** - Small imbalances can become bigger problems

6. **Export data** - Use `--json` flag to save reports for external analysis

7. **Set benchmarks** - Export your monthly reports to track long-term progress
