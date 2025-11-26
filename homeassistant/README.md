# Tindeq Home Assistant Integration

Custom Home Assistant integration for tracking and visualizing Tindeq finger training data.

## Features

This integration provides sensors for:

### Consistency Metrics
- **Training Frequency**: Sessions per week
- **Current Streak**: Consecutive days of training
- **Longest Streak**: Best training streak
- **Morning/Evening Sessions**: Count of sessions by time of day

### Performance Metrics
- **Max Force Trend**: Change percentage over time
- **Average Force Trend**: Change percentage over time
- **Left/Right Balance**: Asymmetry score (100% = perfect balance)

### Recovery & Fatigue
- **Session Fatigue**: Decline in performance within a session
- **Recovery Quality**: Overnight recovery between evening and morning sessions

### General
- **Last Session**: Timestamp of most recent session
- **Total Sessions**: Total number of imported sessions

## Prerequisites

1. **Tindeq Exporter**: The systemd service should be running and importing data
2. **Storage Directory**: You need access to the directory where tindeq data is stored
3. **Python Dependencies**: pandas, pyarrow, numpy (automatically installed)

## Installation

### Method 1: NixOS (Recommended)

If you're running Home Assistant on NixOS, use the packaged component:

1. Add the flake to your inputs:
   ```nix
   inputs.tindeq-exporter.url = "github:fedeizzo/tindeq-exporter";
   ```

2. Add the custom component to your Home Assistant configuration:
   ```nix
   services.home-assistant = {
     enable = true;
     customComponents = [
       inputs.tindeq-exporter.packages.${pkgs.system}.homeassistant-component
     ];
   };
   ```

3. Ensure Home Assistant can access the storage directory:
   ```nix
   users.users.hass.extraGroups = [ "tindeq" ];
   ```

4. Rebuild your system and restart Home Assistant

5. Go to **Settings → Devices & Services → Add Integration**

6. Search for "Tindeq" and configure with your storage path

See `nixos-example.nix` for a complete example configuration.

### Method 2: Manual Installation

1. Copy the `custom_components/tindeq` directory to your Home Assistant `custom_components` folder:
   ```bash
   cp -r homeassistant/custom_components/tindeq /path/to/homeassistant/config/custom_components/
   ```

2. Restart Home Assistant

3. Go to **Settings → Devices & Services → Add Integration**

4. Search for "Tindeq" and click to configure

5. Enter your storage directory path (e.g., `/var/lib/tindeq/tindeq_data`)

### Method 3: HACS (Future)

_This integration is not yet available via HACS but may be added in the future._

## Configuration

### Storage Directory

The storage directory should point to where the systemd service stores data:
- Default: `/var/lib/tindeq/tindeq_data`
- Must be readable by the Home Assistant user
- Should contain `tindeq.db` and parquet files (created by tindeq-exporter)

### Permissions

If Home Assistant runs as a different user than the tindeq service, you may need to:

```bash
# Add homeassistant user to tindeq group
sudo usermod -a -G tindeq homeassistant

# Or make the database readable
sudo chmod -R 755 /var/lib/tindeq
```

### Update Interval

Default: 300 seconds (5 minutes)

You can change this in the integration options:
1. Go to **Settings → Devices & Services**
2. Click on the Tindeq integration
3. Click **Configure**
4. Adjust the update interval

## Usage

### Dashboard Cards

Once configured, sensors will appear with the prefix `sensor.tindeq_*`. You can add them to dashboards:

#### Example: Statistics Card

```yaml
type: entities
title: Training Consistency
entities:
  - entity: sensor.tindeq_training_frequency
    name: Sessions per week
  - entity: sensor.tindeq_current_streak
    name: Current streak
  - entity: sensor.tindeq_longest_streak
    name: Best streak
  - entity: sensor.tindeq_last_session
    name: Last session
```

#### Example: Gauge Card

```yaml
type: gauge
entity: sensor.tindeq_left_right_balance
name: Left/Right Balance
min: 0
max: 100
needle: true
segments:
  - from: 0
    color: '#db4437'
  - from: 85
    color: '#ffa600'
  - from: 95
    color: '#43a047'
```

#### Example: History Graph

```yaml
type: history-graph
title: Performance Trends
entities:
  - entity: sensor.tindeq_max_force_trend
  - entity: sensor.tindeq_avg_force_trend
hours_to_show: 168  # 1 week
```

### Automations

Send notifications when your streak is about to break:

```yaml
automation:
  - alias: "Tindeq: Streak Reminder"
    trigger:
      - platform: time
        at: "20:00:00"
    condition:
      - condition: template
        value_template: "{{ states('sensor.tindeq_last_session') | as_datetime | as_local < now().replace(hour=0, minute=0, second=0) }}"
    action:
      - service: notify.mobile_app
        data:
          title: "Training Reminder"
          message: "Don't break your {{ states('sensor.tindeq_current_streak') }} day streak! 💪"
```

Celebrate milestones:

```yaml
automation:
  - alias: "Tindeq: Streak Milestone"
    trigger:
      - platform: state
        entity_id: sensor.tindeq_current_streak
    condition:
      - condition: template
        value_template: "{{ trigger.to_state.state | int % 10 == 0 and trigger.to_state.state | int > 0 }}"
    action:
      - service: notify.mobile_app
        data:
          title: "Training Milestone! 🏆"
          message: "Amazing! You've reached a {{ trigger.to_state.state }} day streak!"
```

## Troubleshooting

### No data showing

1. Verify the storage directory path is correct
2. Check that tindeq.db exists in the directory
3. Ensure Home Assistant has read permissions
4. Check logs: **Settings → System → Logs**

### Sensors showing "Unknown"

1. Make sure you have imported training data using the systemd service
2. Wait for the first update cycle (default: 5 minutes)
3. Check the coordinator is updating: look for "Tindeq" in the logs

### Permission denied errors

```bash
# Check file permissions
ls -la /var/lib/tindeq/tindeq_data/

# Make readable by Home Assistant
sudo chmod 755 /var/lib/tindeq/tindeq_data
sudo chmod 644 /var/lib/tindeq/tindeq_data/tindeq.db

# Or add to group
sudo usermod -a -G tindeq homeassistant
```

## Architecture

This integration follows the separation of concerns:
- **Systemd Service**: Watches for zip files and imports data into SQLite/Parquet
- **Home Assistant**: Reads the database periodically and exposes sensors
- **No overlap**: HA doesn't import data, systemd doesn't visualize

Data flow:
```
Tindeq App → Export ZIP → Watch Directory → Systemd Import → Storage → HA Sensors → Dashboard
```

## Development

To test locally:
```bash
# Link to Home Assistant config
ln -s $(pwd)/homeassistant/custom_components/tindeq ~/.homeassistant/custom_components/tindeq

# Restart Home Assistant
```

Check logs:
```bash
tail -f ~/.homeassistant/home-assistant.log | grep tindeq
```

## Future Enhancements

- [ ] Per-exercise sensor selection via options
- [ ] Historical data export service
- [ ] Comparison cards (week-over-week)
- [ ] Training load/volume metrics
- [ ] MQTT discovery support
- [ ] Multi-exercise tracking
- [ ] Configurable analytics windows (7/14/30 days)

## License

MIT
