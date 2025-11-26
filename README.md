# Climbing lab

A self-hosted platform to collect all your climbing data and analyze them in one place.

## Available tools

- [Tindeq Progressor Importer]: a tool for importing, storing, and analyzing Tindeq finger strength training data.

- **NixOS Module** systemd service with inotify watching for automatic imports
- **Home Assistant** custom integration with 20+ sensors

## Setup

Using Nix:

```bash
nix develop
nix build
nix run
```

Or with just Poetry:

```bash
poetry install
```

## Deployment

### NixOS Systemd Service

The project includes a NixOS module for automatic tindeq imports via systemd:

```nix
{
  imports = [ inputs.tindeq-exporter.nixosModules.default ];

  services.tindeq-exporter = {
    enable = true;
    watchDirectory = "/var/lib/tindeq/exports";
    databaseDirectory = "/var/lib/tindeq";
    deleteAfterImport = true;
    notifyOnImport = false;
  };
}
```

Features:
- **inotify watching** - Automatically imports new zip files when they appear
- **Automatic cleanup** - Optionally deletes zips after successful import
- **Security hardening** - Runs with minimal privileges, isolated filesystem
- **Systemd integration** - Logs via journald, status via `systemctl`

See `nixos-module/example.nix` for full configuration.

### Home Assistant Integration

Custom component providing 20+ sensors for training metrics:

```nix
services.home-assistant = {
  enable = true;
  customComponents = [
    inputs.tindeq-exporter.packages.${pkgs.system}.homeassistant-component
  ];
};
```

Sensors include from tindeq progressor:
- Training frequency, streaks, consistency
- Performance trends (max/avg force)
- Left/right balance and asymmetry
- Session fatigue and recovery quality
- Peakload current/max values and trends
- Total sessions and last session date

See `homeassistant/README.md` for installation and dashboard examples.