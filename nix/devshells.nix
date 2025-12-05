{ inputs', pkgs, config, ... }:

{
  devshells.default = {
    motd = ''
      {202}🏔️ Climbing-lab devshell{reset}
       $(type -p menu &>/dev/null && menu)
    '';

    commands = [ ];

    packages = with pkgs; [
      (pkgs.python3.withPackages (ps: with ps;
      [
        pandas
        pyarrow
        numpy
        # Dev dependencies
        pytest
        ipython
      ]))
      poetry
      convco

      ruff
      python3Packages.black
    ] ++ config.pre-commit.settings.enabledPackages;

    devshell.startup.pre-commit-hooks.text = config.pre-commit.installationScript;
  };
}
