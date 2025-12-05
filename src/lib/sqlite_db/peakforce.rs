use chrono::DateTime;
use rusqlite::{Connection, types::FromSqlError};

use crate::peakforce::peakforce::{Peakforce, PeakforceError};

pub fn save_peakforce(peakforce: &Peakforce, conn: &mut Connection) -> Result<(), PeakforceError> {
    let saved = conn.execute(
        "
            INSERT INTO peakloads
                (date, tag, comment, unit, type, left_max_weight, right_max_weight)
            VALUES
                (?1, ?2, ?3, ?4, ?5, ?6, ?7)
            ON CONFLICT(date, tag) DO UPDATE SET
                comment = excluded.comment,
                unit = excluded.unit,
                type = excluded.type,
                left_max_weight = excluded.left_max_weight,
                right_max_weight = excluded.right_max_weight;
            ",
        (
            peakforce.date.to_string(),
            peakforce.tag.clone(),
            peakforce.comment.clone(),
            peakforce.unit,
            peakforce.peakforce_type,
            peakforce.left_max_weight,
            peakforce.right_max_weight,
        ),
    )?;

    match saved {
        1 => Ok(()),
        _ => Err(PeakforceError::MultiplePeakforceMeasurements),
    }
}
pub fn list_peakforces(conn: &mut Connection) -> Result<Vec<Peakforce>, PeakforceError> {
    let mut stmt = conn
        .prepare("SELECT date, tag, comment, unit, type, left_max_weight, right_max_weight FROM peakloads ORDER BY date DESC limit 10")?;
    let peakforces = stmt
        .query_map([], |row| {
            Ok(Peakforce {
                date: {
                    let unparsed_date: String = row.get(0)?;

                    let date = DateTime::parse_from_str(&unparsed_date, "%Y-%m-%d %H:%M:%S %z")
                        .map_err(|_| FromSqlError::InvalidType)?;

                    date.into()
                },
                tag: row.get(1)?,
                comment: row.get(2)?,
                unit: row.get(3)?,
                peakforce_type: row.get(4)?,
                left_max_weight: row.get(5)?,
                right_max_weight: row.get(6)?,
            })
        })?
        .collect::<Result<Vec<Peakforce>, _>>()?;

    Ok(peakforces)
}
