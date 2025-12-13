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

      # rust
      openssl
      pkg-config
      sqlite
      sqlite-web
      sqlx-cli
      (rust-bin.stable.latest.default.override {
        extensions = [ "rust-analyzer" "rust-src" "rustfmt" "clippy" ];
      })
      refinery-cli # sql migrations
    ] ++ config.pre-commit.settings.enabledPackages;

    devshell.startup.pre-commit-hooks.text = config.pre-commit.installationScript;
  };
}
