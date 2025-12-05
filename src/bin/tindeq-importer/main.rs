use std::path::Path;

use clap::{Args, Parser, Subcommand};
use rusqlite::Connection;
use tabled::{Table, settings::Style};
use tindeqimporter::{
    cli::peakforce::render_trend_table,
    csv_importer::{custom_session, peakforce::peakforce_from_csv},
    peakforce::peakforce::compute_trend,
    sqlite_db::peakforce::{list_peakforces, save_peakforce},
};

mod embedded {
    use refinery::embed_migrations;
    embed_migrations!("./src/bin/tindeq-importer/sql/migrations");
}

fn db_setup(conn: &mut Connection) {
    embedded::migrations::runner().run(conn).unwrap();
}
#[derive(Parser)]
#[command(version, about, long_about = None)]
struct Cli {
    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand)]
enum Commands {
    Import,
    Peakforce(PeakforceArgs),
}

#[derive(Args)]
struct PeakforceArgs {
    #[command(subcommand)]
    action: PeakforceAction,
}

#[derive(Subcommand)]
enum PeakforceAction {
    List,
    Trend,
}

fn main() {
    let mut conn = Connection::open("./data.db").unwrap();
    db_setup(&mut conn);
    let peakforce_path = Path::new("tindeq_data/peakload_data_left_right_29_11_2025.csv");
    let batch_path = Path::new("tindeq_data/customSession_batch_export_2025_12_09.zip");
    let custom_session_path =
        Path::new("tindeq_data/customSession_2025_12_08_09_34AM_morning on.zip");
    // let peakforce = peakforce_from_csv(peakforce_path).unwrap();
    // save_peakforce(&peakforce, &mut conn).unwrap();
    let cli = Cli::parse();

    match cli.command {
        Commands::Import => custom_session::custom_session_from_csv(custom_session_path).unwrap(),
        Commands::Peakforce(peakforce_args) => match peakforce_args.action {
            PeakforceAction::List => {
                let peakforces = list_peakforces(&mut conn).unwrap();

                let mut table = Table::new(&peakforces);
                table.with(Style::rounded());
                println!(
                    "Peakforce measurements ({}) 💪\n{}",
                    peakforces.len(),
                    table
                );
            }
            PeakforceAction::Trend => {
                let peakforces = list_peakforces(&mut conn).unwrap();
                let report = compute_trend(&peakforces).unwrap();
                render_trend_table(std::io::stdout(), &report).unwrap()
            }
        },
    };
}
