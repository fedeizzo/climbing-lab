use std::io::Write;

use tabled::{
    Tabled,
    settings::{Color, Modify, object::Rows},
};

use crate::peakforce::peakforce::{PeakforceHandSummary, PeakforceSample, PeakforceTrandReport};

#[derive(Tabled)]
struct TrendRow {
    #[tabled(rename = "Hand")]
    hand: String,
    #[tabled(rename = "Stat")]
    stat: String,
    #[tabled(rename = "Date")]
    date: String,
    #[tabled(rename = "Value (kg)")]
    value: String,
}

fn fmt_sample(s: &PeakforceSample) -> (String, String) {
    (
        s.date.format("%Y-%m-%d %H:%M:%S").to_string(),
        format!("{:.2} Kg", s.value),
    )
}

fn rows_for_hand(name: &str, h: &PeakforceHandSummary) -> Vec<TrendRow> {
    // current
    let (d_cur, v_cur) = fmt_sample(&h.current);
    // max
    let (d_max, v_max) = fmt_sample(&h.max);
    // min
    let (d_min, v_min) = fmt_sample(&h.min);

    vec![
        TrendRow {
            hand: name.into(),
            stat: "Current".into(),
            date: d_cur,
            value: v_cur,
        },
        TrendRow {
            hand: "".into(),
            stat: "Max".into(),
            date: d_max,
            value: v_max,
        },
        TrendRow {
            hand: "".into(),
            stat: "Min".into(),
            date: d_min,
            value: v_min,
        },
        TrendRow {
            hand: "".into(),
            stat: "Avg".into(),
            date: "".into(),
            value: format!("{:.2} Kg", h.avg),
        },
        TrendRow {
            hand: "".into(),
            stat: "Change".into(),
            date: "".into(),
            value: "+0.5%".into(),
        },
    ]
}

pub fn render_trend_table<W: Write>(
    mut w: W,
    report: &PeakforceTrandReport,
) -> Result<(), std::io::Error> {
    let mut rows = rows_for_hand("Left", &report.left);
    rows.extend(rows_for_hand("Right", &report.right));

    let mut table = tabled::Table::new(rows);
    table.with(tabled::settings::Style::rounded());
    table.with(Modify::new(Rows::first()).with(Color::FG_BRIGHT_WHITE));

    write!(w, "Peakforce trend analysis ({})\n", report.samples_number)?;
    write!(w, "{table}\n\n")?;
    write!(
        w,
        "Current balance: {}% (Left/Right ratio)\n",
        report.current_imbalance
    )?;
    write!(
        w,
        "Average balance: {}% (Left/Right ratio)\n",
        report.average_imbalance
    )
}
