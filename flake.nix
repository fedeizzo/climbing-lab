{
  description = "Tindeq Exporter - Import and analyze Tindeq finger training data";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
    flake-parts.url = "github:hercules-ci/flake-parts";
    devshell.url = "github:numtide/devshell";
    git-hooks-nix.url = "github:cachix/git-hooks.nix";
  };

  outputs = inputs@{ flake-parts, ... }:
    flake-parts.lib.mkFlake { inherit inputs; } (top@{ config, withSystem, moduleWithSystem, ... }: {
      imports = [
        inputs.devshell.flakeModule
        inputs.git-hooks-nix.flakeModule
      ];
      flake = {
        nixosModules.default = import ./nixos-module;
        nixosModules.tindeq-exporter = import ./nixos-module;
      };
      systems = [ "x86_64-linux" "aarch64-linux" "aarch64-darwin" ];

      perSystem = { config, pkgs, ... }: {
        imports = [
          ./nix/devshells.nix
          ./nix/git-hooks.nix
        ];

        apps.default = {
          type = "app";
          program = "${pkgs.callPackage ./tindeq_exporter { inherit pkgs; }}/bin/tindeq";
        };

        packages.default = pkgs.callPackage ./tindeq_exporter { inherit pkgs; };
        packages.tindeq-exporter = pkgs.callPackage ./tindeq_exporter { inherit pkgs; };
        packages.homeassistant-component = pkgs.callPackage ./homeassistant { };
        # packages.homeassistant-component = pkgs.callPackage ./homeassistant {
        #   # Use buildHomeAssistantComponent from home-assistant package
        #   buildHomeAssistantComponent = pkgs.home-assistant.python.pkgs.buildHomeAssistantComponent;
        #   inherit (pkgs.python3Packages) pandas pyarrow numpy;
        # };
      };
    });
}
