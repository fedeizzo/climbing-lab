{ pkgs }:

pkgs.python3Packages.buildPythonApplication {
  pname = "tindeq-exporter";
  version = "0.1.0";

  src = ../.;
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
    maintainers = [ ];
  };
}
