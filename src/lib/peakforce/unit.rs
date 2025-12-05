use std::fmt::Display;

use rusqlite::types::ValueRef::Text;
use rusqlite::{
    ToSql,
    types::{FromSql, FromSqlError, ToSqlOutput, ValueRef},
};
use tabled::Tabled;

#[derive(Debug, serde::Deserialize, Clone, Copy, Tabled)]
pub enum Unit {
    SI,
}

impl Display for Unit {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "SI")
    }
}

impl TryFrom<&[u8]> for Unit {
    type Error = &'static str;

    fn try_from(value: &[u8]) -> Result<Self, Self::Error> {
        match str::from_utf8(value) {
            Ok(v) => match v {
                "SI" => Ok(Unit::SI),
                _ => Err("unknown unit"),
            },
            Err(_) => Err("invalid UTF-8"),
        }
    }
}

impl FromSql for Unit {
    fn column_result(value: ValueRef<'_>) -> Result<Self, FromSqlError> {
        match value {
            Text(items) => Unit::try_from(items).map_err(|_| FromSqlError::InvalidType),
            _ => Err(FromSqlError::InvalidType),
        }
    }
}

impl ToSql for Unit {
    fn to_sql(&self) -> rusqlite::Result<ToSqlOutput<'_>> {
        match self {
            Self::SI => Ok("SI".into()),
        }
    }
}
