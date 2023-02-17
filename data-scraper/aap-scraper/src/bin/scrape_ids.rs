use std::{
    collections::HashSet,
    fs::{read_to_string, File},
    io::{BufRead, BufReader, BufWriter, Write},
    ops::Not,
    sync::Mutex,
};

use rayon::{
    prelude::{IntoParallelIterator, ParallelIterator},
    ThreadPoolBuilder,
};
use regex::Regex;
use ureq::AgentBuilder;

use aap_scraper::{Pet, Result};

fn main() -> Result<()> {
    let agent = AgentBuilder::new().user_agent("firefox").build();
    let url = "https://www.adoptapet.com/";

    let old_data: Vec<Pet> = read_to_string("dogs.data")?
        .lines()
        .map(|l| serde_json::from_str(l).map_err(Into::into))
        .collect::<Result<_>>()?;

    let average_photos =
        old_data.iter().map(|p| p.pet_photos.len()).sum::<usize>() as f64 / old_data.len() as f64;
    dbg!(average_photos);

    let old_ids: HashSet<_> = old_data.iter().map(|p| p.pet_id).collect();

    let csv = Mutex::new(BufWriter::new(
        File::options()
            .create(true)
            .write(true)
            .append(true)
            .open("dogs.data")?,
    ));

    let r_data = Regex::new(r#"viewData: (.+) }">"#)?;
    let r_quote = Regex::new(r#"&quot;"#)?;
    let r_slash = Regex::new(r#"\\/"#)?;

    let mut ids: Vec<_> = std::fs::read_to_string("dogs.csv")?
        .lines()
        .map(|l| l.parse::<i32>())
        .collect::<std::result::Result<_, _>>()?;

    println!("total number of ids: {}", ids.len());

    ids.retain(|i| old_ids.contains(i).not());

    println!("number of ids remaining: {}", ids.len());

    let old_len = ids.len();

    ids.sort();
    ids.dedup();

    println!("removed {} duplicates", old_len - ids.len());

    ThreadPoolBuilder::new().num_threads(4).build_global()?;
    ids.into_par_iter()
        .map(|id| {
            let test = agent.get(&format!("{url}pet/{id}")).call()?;

            let lines = BufReader::new(test.into_reader()).lines();

            let pets = lines
                .filter_map(|l| {
                    let line = l.ok()?;
                    let json = r_data.captures(&line)?.get(1)?.as_str();
                    let json = r_quote.replace_all(json, r#"""#);
                    let json = r_slash.replace_all(&json, "/");
                    let pet = serde_json::from_str(&json);
                    if pet.is_err() {
                        dbg!(&pet);
                    }
                    pet.ok()
                })
                .collect::<Vec<Pet>>();

            let mut csv = csv.lock().map_err(|_| "poison error")?;
            for pet in pets {
                writeln!(csv, "{}", serde_json::to_string(&pet)?)?;
            }
            csv.flush()?;
            drop(csv);

            println!("pet with {id} done");
            Ok(())
        })
        .collect::<Result<_>>()?;

    Ok(())
}
