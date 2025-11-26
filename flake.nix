{
  description = "Tindeq Exporter - Import and analyze Tindeq finger training data";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    {
      # NixOS module
      nixosModules.default = import ./nixos-module;
      nixosModules.tindeq-exporter = import ./nixos-module;
    } // flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};

        # Build the package using nixpkgs python packages
        tindeq-exporter = pkgs.python3Packages.buildPythonApplication {
          pname = "tindeq-exporter";
          version = "0.1.0";

          src = ./.;
          format = "pyproject";

          nativeBuildInputs = with pkgs.python3Packages; [
            poetry-core
          ];

          propagatedBuildInputs = with pkgs.python3Packages; [
            pandas
            pyarrow
            numpy
          ];

          # Don't check during build (tests require data files)
          doCheck = false;

          meta = with pkgs.lib; {
            description = "Import and analyze Tindeq finger training data";
            homepage = "https://github.com/fedeizzo/tindeq-exporter";
            license = licenses.mit;
            maintainers = [];
          };
        };

        # Python environment for development
        pythonEnv = pkgs.python3.withPackages (ps: with ps; [
          pandas
          pyarrow
          numpy
          # Dev dependencies
          pytest
          ipython
          jupyter
        ]);
      in
      {
        packages = {
          default = tindeq-exporter;
          tindeq-exporter = tindeq-exporter;
        };

        apps.default = {
          type = "app";
          program = "${tindeq-exporter}/bin/tindeq";
        };

        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            pythonEnv
            poetry

            ruff
            python3Packages.black
          ];

          shellHook = ''
            echo "🏔️  Tindeq Exporter Development Environment"
            echo ""
            echo "Quick start:"
            echo "  poetry install    # Install package with dev dependencies"
            echo "  poetry shell      # Activate virtualenv"
            echo "  tindeq --help     # Run CLI"
            echo ""
            echo "Or build with nix:"
            echo "  nix build         # Build the package"
            echo "  nix run           # Run the CLI"
            echo ""
          '';
        };
      }
    );
}
