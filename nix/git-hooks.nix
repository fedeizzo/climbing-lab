{ pkgs, ... }:

let
  statix-config = pkgs.writeText "statix.toml" ''disabled = [ "unquoted_uri" ]'';
in
{
  pre-commit = {
    check.enable = true;

    settings = {
      addGcRoot = true;

      hooks = {
        # Filesystem
        check-added-large-files.enable = true;
        check-case-conflicts.enable = true; # Insensitive filesystem
        end-of-file-fixer.enable = true;
        trim-trailing-whitespace.enable = true;

        # Bash
        check-executables-have-shebangs.enable = true;
        check-shebang-scripts-are-executable.enable = true;

        # Languages
        check-json.enable = true;
        check-toml.enable = true;

        ## Nix
        deadnix.enable = true;
        nil.enable = true;
        nixpkgs-fmt.enable = true;
        statix.enable = true;
        statix.settings.config = "${statix-config}";

        # Misc
        actionlint.enable = true; # GitHub actions
        detect-private-keys.enable = true;
        ripsecrets = {
          enable = true; # Secret keys
          excludes = [ ];
        };
        typos = {
          enable = false;
          excludes = [
            "./homeassistant/custom_components/tindeq/__init__.py"
          ];
        };
      };
    };
  };
}
