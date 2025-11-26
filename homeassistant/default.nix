{ buildHomeAssistantComponent
, pandas
, pyarrow
, numpy
}:

buildHomeAssistantComponent rec {
  owner = "fedeizzo";
  domain = "tindeq";
  version = "0.1.0";

  src = ./custom_components/tindeq;

  # Python dependencies required by the component
  dependencies = [
    pandas
    pyarrow
    numpy
  ];

  meta = {
    description = "Home Assistant integration for Tindeq finger training data";
    homepage = "https://github.com/fedeizzo/tindeq-exporter";
    license = "MIT";
  };
}
