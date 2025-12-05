use std::{
    fs::{self, File},
    io,
    path::Path,
};

use chrono::{DateTime, Duration, Local, NaiveDateTime, TimeZone, offset::LocalResult};
use serde::{Deserialize, Deserializer, de::Error};
use zip::ZipArchive;

use crate::{
    custom_session::custom_session::{CustomSession, CustomSessionError},
    peakforce::{peakforce_type::Type, unit::Unit},
};

#[derive(Debug, serde::Deserialize)]
struct Settings {
    #[serde(deserialize_with = "swap_dt::deserialize")]
    #[serde(rename(deserialize = "Date"))]
    date: DateTime<Local>,
    #[serde(rename(deserialize = "Tag"))]
    tag: String,
    #[serde(rename(deserialize = "Comment"))]
    comment: String,
    #[serde(rename(deserialize = "Countdown Time"))]
    countdown_time: i32,
    #[serde(rename(deserialize = "Unit"))]
    unit: String,
    #[serde(rename(deserialize = "Left/Right"))]
    left_right: String,
    #[serde(rename(deserialize = "Alternate Mode"))]
    alternate_mode: String,
    #[serde(rename(deserialize = "Initial Side"))]
    initial_side: String,
    #[serde(rename(deserialize = "Switch Side Time"))]
    switch_side_time: i32,
}

#[derive(Debug, serde::Deserialize)]
struct TimeSample {
    #[serde(rename(deserialize = "Type"))]
    sample_type: String, // TODO this should be an enum
    #[serde(rename(deserialize = "Start Time"))]
    start_time: Duration,
    #[serde(rename(deserialize = "End Time"))]
    end_time: Duration,
    #[serde(rename(deserialize = "Duration"))]
    duration: Duration,
    #[serde(rename(deserialize = "Side"))]
    side: String, // TODO enum
    #[serde(rename(deserialize = "Target Low (%)"))]
    target_low_percentage: u8,
    #[serde(rename(deserialize = "Target High (%)"))]
    target_high_percentage: u8,
    #[serde(rename(deserialize = "MVC"))]
    #[serde(deserialize_with = "deserialize_datamap")]
    mvc: MVCSample,
    #[serde(rename(deserialize = "Set"))]
    set: u8,
    #[serde(rename(deserialize = "Rep"))]
    rep: u8,
    #[serde(rename(deserialize = "Name"))]
    name: String,
}

#[derive(Debug)]
struct MVCSample {
    left: Option<f64>,
    right: Option<f64>,
    single: Option<f64>,
}

fn deserialize_datamap<'de, D>(deserializer: D) -> Result<MVCSample, D::Error>
where
    D: Deserializer<'de>,
{
    let value = String::deserialize(deserializer)?;

    let ciao = value.trim().to_string();
    let ciao2 = ciao.get(8..);

    println!("{:?}", ciao2);

    Ok(MVCSample {
        left: Some(0.0),
        right: Some(0.0),
        single: Some(0.0),
    })
}

pub fn custom_session_from_csv(path: &Path) -> Result<(), CustomSessionError> {
    let tmpdir = tempdir::TempDir::new("tindeq-importer")?;
    let file = File::open(path)?;

    let mut archive = ZipArchive::new(file)?;
    archive.extract(tmpdir.path())?;

    let paths = fs::read_dir(tmpdir.path()).unwrap();

    for path in paths {
        println!("Name: {}", path.unwrap().path().display())
    }

    println!("{:?}", get_settings(tmpdir.path())?);
    get_timeline(tmpdir.path())?;

    tmpdir.close()?;
    Ok(())
}

fn get_settings(dir: &Path) -> Result<Settings, CustomSessionError> {
    let mut reader = csv::Reader::from_path(dir.join("settings.csv"))?;
    let mut settings: Vec<Settings> = reader.deserialize::<Settings>().collect::<Result<_, _>>()?;

    match settings.len() {
        0 => Err(CustomSessionError::MissingMeasurement),
        1 => Ok(settings.remove(0)),
        _ => Err(CustomSessionError::MultipleMeasurements),
    }
}

fn get_timeline(dir: &Path) -> Result<Vec<TimeSample>, CustomSessionError> {
    let mut reader = csv::Reader::from_path(dir.join("timeline.csv"))?;
    let timeline: Vec<TimeSample> = reader
        .deserialize::<TimeSample>()
        .collect::<Result<_, _>>()?;

    println!("{:?}", timeline);

    Ok(timeline)
}

// TODO refactor this into a common component
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
