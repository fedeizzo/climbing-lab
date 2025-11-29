# Example NixOS configuration for Home Assistant with Tindeq custom component
#
# This demonstrates how to integrate the Tindeq custom component into your
# NixOS Home Assistant setup.
#
# Usage:
# 1. Import this configuration in your NixOS config
# 2. Adjust paths and settings as needed
# 3. The component will be automatically installed to Home Assistant

{ config, pkgs, inputs, ... }:

{
  # Ensure tindeq-exporter flake is added to your inputs:
  # inputs.tindeq-exporter.url = "github:fedeizzo/tindeq-exporter";

  services.home-assistant = {
    enable = true;

    # Custom components installation
    customComponents = [
      # Add the Tindeq component from the flake
      inputs.tindeq-exporter.packages.${pkgs.system}.homeassistant-component

      # Or if using a local path:
      # (pkgs.callPackage /path/to/tindeq-exporter/homeassistant {
      #   buildHomeAssistantComponent = pkgs.home-assistant.python.pkgs.buildHomeAssistantComponent;
      #   inherit (pkgs.python3Packages) pandas pyarrow numpy;
      # })
    ];

    # Ensure Home Assistant can access the tindeq storage directory
    extraComponents = [
      "met"  # Weather
      "radio_browser"
      # ... other components
    ];

    config = {
      # Home Assistant configuration.yaml
      default_config = {};

      http = {
        server_port = 8123;
        trusted_proxies = [ "127.0.0.1" ];
      };

      # The Tindeq integration will be configured through the UI
      # after Home Assistant starts
    };
  };

  # If using the systemd import service, ensure directories are accessible
  # by both the tindeq-import service and Home Assistant
  users.users.hass.extraGroups = [ "tindeq" ];

  # Example: Use the tindeq-exporter systemd service alongside Home Assistant
  services.tindeq-exporter = {
    enable = true;
    watchDirectory = "/var/lib/tindeq/exports";
    databaseDirectory = "/var/lib/tindeq";
    deleteAfterImport = true;
  };
}

# After applying this configuration:
#
# 1. Home Assistant will have the Tindeq integration available
# 2. Go to Settings → Devices & Services → Add Integration
# 3. Search for "Tindeq" and configure with: /var/lib/tindeq/tindeq_data
# 4. Sensors will appear as sensor.tindeq_*
#
# Troubleshooting:
#
# - Check HA logs: journalctl -u home-assistant -f
# - Verify component installed: ls /var/lib/hass/custom_components/
# - Check permissions: sudo -u hass ls -la /var/lib/tindeq/tindeq_data/
