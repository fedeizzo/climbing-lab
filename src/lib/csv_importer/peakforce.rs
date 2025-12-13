use std::path::Path;

use crate::peakforce::peakforce::{Peakforce, PeakforceError};

pub fn peakforce_from_csv(path: &Path) -> Result<Peakforce, PeakforceError> {
    let mut reader = csv::Reader::from_path(path)?;

    let mut peakforces: Vec<Peakforce> = reader
        .deserialize::<Peakforce>()
        .collect::<Result<_, _>>()?;

    match peakforces.len() {
        0 => Err(PeakforceError::MissingPeakforceMeasurement),
        1 => Ok(peakforces.remove(0)),
        _ => Err(PeakforceError::MultiplePeakforceMeasurements),
    }
}
