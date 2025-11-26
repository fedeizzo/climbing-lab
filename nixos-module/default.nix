{ config, lib, pkgs, ... }:

with lib;

let
  cfg = config.services.tindeq-exporter;
in
{
  options.services.tindeq-exporter = {
    enable = mkEnableOption "Tindeq training data importer";

    package = mkOption {
      type = types.package;
      default = pkgs.callPackage ../. { };
      defaultText = literalExpression "pkgs.callPackage ../. { }";
      description = "The tindeq-exporter package to use";
    };

    user = mkOption {
      type = types.str;
      default = "tindeq";
      description = "User account under which the service runs";
    };

    group = mkOption {
      type = types.str;
      default = "tindeq";
      description = "Group under which the service runs";
    };

    watchDirectory = mkOption {
      type = types.path;
      example = "/var/lib/tindeq/exports";
      description = "Directory to watch for new Tindeq export zip files";
    };

    databaseDirectory = mkOption {
      type = types.path;
      default = "/var/lib/tindeq/database";
      description = "Directory where the SQLite database will be stored";
    };

    deleteAfterImport = mkOption {
      type = types.bool;
      default = true;
      description = "Whether to delete zip files after successful import";
    };

    notifyOnImport = mkOption {
      type = types.bool;
      default = false;
      description = "Send system notification on successful import";
    };
  };

  config = mkIf cfg.enable {
    # Create user and group
    users.users.${cfg.user} = mkIf (cfg.user == "tindeq") {
      isSystemUser = true;
      group = cfg.group;
      home = cfg.databaseDirectory;
      createHome = true;
      description = "Tindeq exporter service user";
    };

    users.groups.${cfg.group} = mkIf (cfg.group == "tindeq") { };

    # Ensure directories exist with correct permissions
    systemd.tmpfiles.rules = [
      "d '${cfg.watchDirectory}' 0755 ${cfg.user} ${cfg.group} -"
      "d '${cfg.databaseDirectory}' 0755 ${cfg.user} ${cfg.group} -"
    ];

    # Systemd service for importing data
    systemd.services.tindeq-import = {
      description = "Import Tindeq training data";
      serviceConfig = {
        Type = "oneshot";
        User = cfg.user;
        Group = cfg.group;

        # Import all zip files in watch directory
        ExecStart = pkgs.writeShellScript "tindeq-import" ''
          set -e

          export STORAGE_DIR="${cfg.databaseDirectory}/tindeq_data"

          # Find all zip files
          shopt -s nullglob
          zipfiles=(${cfg.watchDirectory}/*.zip)

          if [ ''${#zipfiles[@]} -eq 0 ]; then
            echo "No zip files found in ${cfg.watchDirectory}"
            exit 0
          fi

          echo "Found ''${#zipfiles[@]} zip file(s) to import"

          for zipfile in "''${zipfiles[@]}"; do
            echo "Importing: $zipfile"

            # Detect if it's a batch export by filename
            if [[ "$(basename "$zipfile")" == *"batch_export"* ]]; then
              ${cfg.package}/bin/tindeq --storage-dir "$STORAGE_DIR" \
                import --batch "$zipfile" ${optionalString cfg.deleteAfterImport "--delete-after"}
            else
              ${cfg.package}/bin/tindeq --storage-dir "$STORAGE_DIR" \
                import "$zipfile" ${optionalString cfg.deleteAfterImport "--delete-after"}
            fi

            if [ $? -eq 0 ]; then
              echo "Successfully imported: $zipfile"
              ${optionalString cfg.notifyOnImport ''
                ${pkgs.libnotify}/bin/notify-send "Tindeq Import" "Successfully imported $(basename "$zipfile")"
              ''}
            else
              echo "Failed to import: $zipfile"
              ${optionalString cfg.notifyOnImport ''
                ${pkgs.libnotify}/bin/notify-send -u critical "Tindeq Import Failed" "Failed to import $(basename "$zipfile")"
              ''}
            fi
          done
        '';

        # Security hardening
        PrivateTmp = true;
        ProtectSystem = "strict";
        ProtectHome = true;
        ReadWritePaths = [ cfg.watchDirectory cfg.databaseDirectory ];
        NoNewPrivileges = true;

        # Logging
        StandardOutput = "journal";
        StandardError = "journal";
      };
    };

    # Systemd path unit for watching directory
    systemd.paths.tindeq-import = {
      description = "Watch for new Tindeq training data exports";
      wantedBy = [ "multi-user.target" ];

      pathConfig = {
        # Trigger when any file is created or moved into the directory
        PathChanged = cfg.watchDirectory;
        # Only trigger for files ending in .zip
        Unit = "tindeq-import.service";
        # Make changes trigger immediately
        MakeDirectory = true;
        DirectoryMode = "0755";
      };
    };
  };
}
