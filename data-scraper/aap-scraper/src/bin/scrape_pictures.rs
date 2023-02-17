use std::{
    collections::HashSet,
    fs::{read_to_string, File},
    io::{copy, BufWriter, Write},
    ops::Not,
    sync::Mutex,
};

use indicatif::{ParallelProgressIterator, ProgressStyle};
use rayon::{
    prelude::{IntoParallelIterator, ParallelIterator},
    ThreadPoolBuilder,
};
use regex::Regex;
use ureq::AgentBuilder;

use aap_scraper::{Pet, PetPhoto, Result};

fn main() -> Result<()> {
    let agent = AgentBuilder::new().user_agent("firefox").build();

    let old_ids: HashSet<_> = read_to_string("dog_pics.data")?
        .lines()
        .map(|l| serde_json::from_str(l).map_err(Into::into))
        .collect::<Result<Vec<PetPhoto>>>()?
        .into_iter()
        .filter(|p| p.saved_path.is_some())
        .map(|p| p.display_photo_url)
        .collect();

    let r_name = Regex::new(r#"adoptapet\.com/(.+).(jpe?g|png)"#)?;

    let mut data = read_to_string("dogs.data")?
        .lines()
        .map(|l| serde_json::from_str(l).map_err(Into::into))
        .collect::<Result<Vec<Pet>>>()?
        .into_iter()
        .flat_map(|mut p| {
            for pic in &mut p.pet_photos {
                let Some(captures) = r_name.captures(&pic.display_photo_url) else {
                    panic!("{pic:?}");
                };
                let path = captures.get(1).unwrap().as_str().replace('/', "-");

                pic.saved_path = Some(format!("pictures/{path}.jpg").into());
                pic.pet_id = Some(p.pet_id);
            }
            p.pet_photos
        })
        .filter(|p| old_ids.contains(&p.display_photo_url).not())
        .collect::<Vec<_>>();

    let csv = Mutex::new(BufWriter::new(
        File::options()
            .create(true)
            .write(true)
            .append(true)
            .open("dog_pics.data")?,
    ));

    println!("total number of ids: {}", data.len());

    let old_len = data.len();

    data.sort();
    data.dedup();

    println!("removed {} duplicates", old_len - data.len());

    let style = ProgressStyle::with_template("{wide_bar} [{elapsed} | {eta}] {pos}/{len}").unwrap();

    ThreadPoolBuilder::new().num_threads(4).build_global()?;
    data.into_par_iter()
        .progress_with_style(style)
        .map(|picture| {
            let url = &&picture.display_photo_url;
            let pic_response = match agent.get(url).call() {
                Ok(t) => t,
                Err(e) => {
                    println!("Error: {e}");
                    return Ok(());
                }
            };

            let mut file = File::create(picture.saved_path.as_ref().unwrap())?;
            copy(&mut pic_response.into_reader(), &mut file)?;

            let mut csv = csv.lock().map_err(|_| "poison error")?;

            writeln!(csv, "{}", serde_json::to_string(&picture)?)?;

            Ok(())
        })
        .collect::<Result<_>>()?;

    Ok(())
}
