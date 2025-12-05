use std::io;

use chrono::{DateTime, Duration, Local};
use thiserror::Error;
use zip::result::ZipError;

use crate::peakforce::unit::Unit;

pub struct CustomSession {
    date: DateTime<Local>,
    tag: String,
    comment: String,
    countdown_time: Duration,
    unit: Unit,             // TODO refactor Unit in a common package
    left_right: bool, // TODO probably worth to change the db schema to be use the type enum from shared with peakforce
    alternate_mode: String, // TODO probably worth to change it to bool
    initial_side: String, // TODO enum
    switch_side_time: Duration,
}

#[derive(Debug, Error)]
pub enum CustomSessionError {
    #[error("todo")]
    TmpDir(#[from] io::Error),
    #[error("todo")]
    Zip(#[from] ZipError),
    #[error("todo")]
    Csv(#[from] csv::Error),
    #[error("multiple peakforce measurements")]
    MultipleMeasurements,
    #[error("missing peakforce measurement")]
    MissingMeasurement,
}
