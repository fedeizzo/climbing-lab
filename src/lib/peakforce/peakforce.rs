use std::ops::Div;

use chrono::{DateTime, Local, NaiveDateTime, TimeZone, offset::LocalResult};
use ordered_float::{FloatIsNan, NotNan};
use serde::{Deserialize, Deserializer, de::Error};
use tabled::Tabled;
use thiserror::Error;

use crate::peakforce::{peakforce_type::Type, unit::Unit};

#[derive(Debug, Error)]
pub enum PeakforceError {
    #[error("cannot parse the peakforce measurement")]
    Csv(#[from] csv::Error),
    #[error("error while doing sqlite operation")]
    Sqlite(#[from] rusqlite::Error),
    #[error("todo")]
    OrderedFloat(#[from] FloatIsNan),
    #[error("multiple peakforce measurements")]
    MultiplePeakforceMeasurements,
    #[error("missing peakforce measurement")]
    MissingPeakforceMeasurement,
    #[error("invalid date for the peakforce measurement")]
    InvalidDate,
}

#[derive(Debug, serde::Deserialize, Tabled)]
pub struct Peakforce {
    #[serde(deserialize_with = "swap_dt::deserialize")]
    #[tabled(rename = "Date")]
    pub date: chrono::DateTime<Local>,
    #[tabled(rename = "Tag")]
    pub tag: String,
    #[tabled(rename = "Comment")]
    pub comment: String,
    #[tabled(rename = "Unit")]
    pub unit: Unit,
    #[serde(rename(deserialize = "type"))]
    #[tabled(rename = "Measurement type")]
    pub peakforce_type: Type,
    #[tabled(rename = "Max weight with left hand")]
    #[serde(rename(deserialize = "left max weight"))]
    pub left_max_weight: f64,
    #[tabled(rename = "Max weight with right hand")]
    #[serde(rename(deserialize = "right max weight"))]
    pub right_max_weight: f64,
}

#[derive(Debug, Clone, Copy, PartialEq, PartialOrd, Eq, Ord)]
pub(crate) struct PeakforceSample {
    pub value: NotNan<f64>,
    pub date: DateTime<Local>,
}

#[derive(Debug)]
pub(crate) struct PeakforceHandSummary {
    pub current: PeakforceSample,
    pub max: PeakforceSample,
    pub min: PeakforceSample,
    pub avg: f64,
}

#[derive(Debug)]
pub struct PeakforceTrandReport {
    pub(crate) left: PeakforceHandSummary,
    pub(crate) right: PeakforceHandSummary,
    pub(crate) samples_number: u32,
    pub(crate) current_imbalance: u8,
    pub(crate) average_imbalance: u8,
}

fn get_hand_summary(
    samples: &Vec<PeakforceSample>,
) -> Result<PeakforceHandSummary, PeakforceError> {
    let max = samples
        .iter()
        .max()
        .ok_or(PeakforceError::MissingPeakforceMeasurement)?;
    let min = samples
        .iter()
        .min()
        .ok_or(PeakforceError::MissingPeakforceMeasurement)?;
    let sum: f64 = samples.iter().map(|s| s.value.into_inner()).sum::<f64>();
    let current = samples
        .last()
        .ok_or(PeakforceError::MissingPeakforceMeasurement)?;

    Ok(PeakforceHandSummary {
        current: *current,
        max: *max,
        min: *min,
        avg: sum / samples.len() as f64,
    })
}

pub fn compute_trend(peakforces: &Vec<Peakforce>) -> Result<PeakforceTrandReport, PeakforceError> {
    let mut left_measurements = Vec::new();
    let mut right_measurements = Vec::new();

    for peakforce in peakforces {
        let left = PeakforceSample {
            value: NotNan::new(peakforce.left_max_weight)?,
            date: peakforce.date,
        };
        let right = PeakforceSample {
            value: NotNan::new(peakforce.right_max_weight)?,
            date: peakforce.date,
        };
        left_measurements.push(left);
        right_measurements.push(right);
    }

    let left_summary = get_hand_summary(&left_measurements)?;
    let right_summary = get_hand_summary(&right_measurements)?;
    let current_imbalance = left_summary
        .current
        .value
        .div(right_summary.current.value)
        .into_inner()
        * 100 as f64;
    let average_imbalance = left_summary.avg / right_summary.avg * 100 as f64;

    Ok(PeakforceTrandReport {
        left: left_summary,
        right: right_summary,
        samples_number: left_measurements.len() as u32,
        current_imbalance: current_imbalance as u8,
        average_imbalance: average_imbalance as u8,
    })
}

mod swap_dt {
    pub use super::deserialize;
}

pub fn deserialize<'de, D>(d: D) -> Result<DateTime<Local>, D::Error>
where
    D: Deserializer<'de>,
{
    let s = String::deserialize(d)?;
    const F: &str = "%Y-%d-%m %H:%M:%S";
    let dt = NaiveDateTime::parse_from_str(&s, F)
        .map_err(|_| Error::custom("cannot parse the date using YYYY-dd-mm HH:MM:SS format"))?;

    match Local.from_local_datetime(&dt) {
        LocalResult::Single(v) => Ok(v),
        LocalResult::Ambiguous(_, _) => Err(Error::custom("ambiguous local datetime")),
        LocalResult::None => Err(Error::custom("invalid local datetime")),
    }
}
