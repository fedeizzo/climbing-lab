use std::fmt::Display;

use rusqlite::types::ValueRef::Text;
use rusqlite::{
    ToSql,
    types::{FromSql, FromSqlError, ValueRef},
};
use tabled::Tabled;

#[derive(Debug, serde::Deserialize, Clone, Copy, Tabled)]
pub enum Type {
    #[serde(rename(deserialize = "left/right"))]
    LeftRight,
}

impl Display for Type {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "left/right")
    }
}

impl TryFrom<&[u8]> for Type {
    type Error = &'static str;

    fn try_from(value: &[u8]) -> Result<Self, Self::Error> {
        match str::from_utf8(value) {
            Ok(v) => match v {
                "left/right" => Ok(Type::LeftRight),
                _ => Err("unknown type"),
            },
            Err(_) => Err("invalid UTF-8"),
        }
    }
}

impl FromSql for Type {
    fn column_result(value: ValueRef<'_>) -> Result<Self, FromSqlError> {
        match value {
            Text(items) => Type::try_from(items).map_err(|_| FromSqlError::InvalidType),
            _ => Err(FromSqlError::InvalidType),
        }
    }
}

impl ToSql for Type {
    fn to_sql(&self) -> rusqlite::Result<rusqlite::types::ToSqlOutput<'_>> {
        match self {
            Self::LeftRight => Ok("left/right".into()),
        }
    }
}
