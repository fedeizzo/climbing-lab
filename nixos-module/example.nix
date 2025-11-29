# Example NixOS configuration for tindeq-exporter service
#
# This file demonstrates how to integrate the tindeq-exporter systemd service
# into your NixOS system configuration.
#
# Usage:
# 1. Add this to your flake.nix inputs:
#    inputs.tindeq-exporter.url = "github:yourusername/tindeq-exporter";
#
# 2. Import the module in your NixOS configuration:
#    imports = [ inputs.tindeq-exporter.nixosModules.default ];
#
# 3. Configure the service as shown below

{ config, pkgs, ... }:

{
  # Import the tindeq-exporter module
  # (In a real configuration, this would be imported via flake inputs)
  imports = [ ./default.nix ];

  # Enable and configure the tindeq-exporter service
  services.tindeq-exporter = {
    enable = true;

    # Directory to watch for new zip files
    # The systemd path unit will trigger imports when files appear here
    watchDirectory = "/home/yourusername/tindeq/exports";

    # Directory where the SQLite database and parquet files will be stored
    databaseDirectory = "/var/lib/tindeq";

    # Automatically delete zip files after successful import
    deleteAfterImport = true;

    # Optional: customize the user/group (defaults to "tindeq")
    # user = "tindeq";
    # group = "tindeq";

    # Optional: use a custom package build
    # package = pkgs.callPackage ./path/to/custom/build.nix { };
  };

  # Example: Give your user read access to the database
  # users.users.yourusername.extraGroups = [ "tindeq" ];
}

# After applying this configuration:
#
# 1. The service will automatically start watching the directory
# 2. Drop zip files into /home/yourusername/tindeq/exports
# 3. They will be imported automatically via inotify
# 4. View logs with: journalctl -u tindeq-import.service
# 5. Check service status: systemctl status tindeq-import.path
#
# Manual import trigger:
#   systemctl start tindeq-import.service
#
# Query the data using the CLI:
#   tindeq --storage-dir /var/lib/tindeq/tindeq_data list
#   tindeq --storage-dir /var/lib/tindeq/tindeq_data analyze consistency --days 30
