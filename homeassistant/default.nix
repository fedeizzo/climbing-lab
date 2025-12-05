{ buildHomeAssistantComponent, python3Packages }:

buildHomeAssistantComponent {
  owner = "fedeizzo";
  domain = "tindeq";
  version = "0.1.0";

  src = ./custom_components/tindeq;

  # Python dependencies required by the component
  dependencies = with python3Packages; [
    pandas
    pyarrow
    numpy
  ] ++ [
    (pkgs.callPackage ../tindeq_exporter { })
  ];

  meta = {
    description = "Home Assistant integration for Tindeq finger training data";
    homepage = "https://github.com/fedeizzo/tindeq-exporter";
    license = "MIT";
  };
}
