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
      default = pkgs.callPackage ../tindeq_exporter/. { };
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
  };

  config = mkIf cfg.enable {
    # Create user and group
    users.users.${cfg.user} = mkIf (cfg.user == "tindeq") {
      isSystemUser = true;
      inherit group;
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
          export DELETE_APPENDIX=${optionalString cfg.deleteAfterImport "--delete-after"}
          export SHOULD_DELETE=${builtins.toString cfg.deleteAfterImport} # check using "1" for true and "" for false
          export WATCH_DIR="${cfg.watchDirectory}"
          export TINDEQ="${cfg.package}/bin/tindeq"

          shopt -s nullglob
          zipfiles=(''${WATCH_DIR}/*.zip)
          peakloadfiles=(''${WATCH_DIR}/peakload_*)

          if [ ''${#zipfiles[@]} -eq 0 ] && [ ''${#peakloadfiles[@]} -eq 0 ]; then
              echo "No zip or peak load files found in $WATCH_DIR"
              exit 0
          fi
          echo "Found ''${#zipfiles[@]} zip file(s) to import"
          echo "Found ''${#peakloadfiles[@]} peak file(s) to import"

          # tindeq custom sessions
          for zipfile in "''${zipfiles[@]}"
          do
              echo "Importing: $zipfile"

              # Detect if it's a batch export by filename
              if [[ "$(basename "$zipfile")" == *"batch_export"* ]]; then
                  ''${TINDEQ} --storage-dir "$STORAGE_DIR" import --batch "$zipfile" $DELETE_APPENDIX
              else
                  ''${TINDEQ} --storage-dir "$STORAGE_DIR" import "$zipfile" $DELETE_APPENDIX
              fi

              if [ $? -eq 0 ]; then
                  echo "Successfully imported: $zipfile"
              else
                  echo "Failed to import: $zipfile"
              fi
          done

          for peakloadfile in "''${peakloadfiles[@]}"; do
              echo "Importing: $peakloadfile"

              ''${TINDEQ} --storage-dir "$STORAGE_DIR" peakload import "$peakloadfile"

              if [[ ''${SHOULD_DELETE} == 1 ]]; then
                  rm $peakloadfile
              fi

              if [ $? -eq 0 ]; then
                  echo "Successfully imported: $peakloadfile"
              else
                  echo "Failed to import: $peakloadfile"
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
        Unit = "tindeq-import.service";
        MakeDirectory = true;
        DirectoryMode = "0755";
      };
    };
  };
}
