mod audio;
use crossbeam_channel::unbounded;
use std::fs::{self, File};
use std::io::{self, Write};
use std::path::Path;
use vosk::{Model, Recognizer};

const MODEL_URL: &str = "https://alphacephei.com";
const MODEL_DIR: &str = "vosk-model-small-en-us";

fn ensure_model_exists() -> Result<(), Box<dyn std::error::Error>> {
    let target_path = Path::new(MODEL_DIR);
    
    // If the folder already exists, skip downloading entirely
    if target_path.exists() {
        return Ok(());
    }

    println!("[RUST ASR] Model folder '{}' not found.", MODEL_DIR);
    println!("[RUST ASR] Attempting to download from remote repository...");
    println!("[RUST ASR] URL: {}", MODEL_URL);

    // 1. Download the ZIP file over a synchronous stream
    let response = ureq::get(MODEL_URL).call()?;
    let mut reader = response.into_reader();
    
    let zip_filename = "model_temp.zip";
    let mut temp_file = File::create(zip_filename)?;
    io::copy(&mut reader, &mut temp_file)?;
    println!("[RUST ASR] Download complete. Extracting files...");

    // 2. Extract the downloaded ZIP file archive
    let file = File::open(zip_filename)?;
    let mut archive = zip::ZipArchive::new(file)?;

    for i in 0..archive.len() {
        let mut file = archive.by_index(i)?;
        let outpath = match file.enclosed_name() {
            Some(path) => path.to_owned(),
            None => continue,
        };

        if file.name().ends_with('/') {
            fs::create_dir_all(&outpath)?;
        } else {
            if let Some(p) = outpath.parent() {
                if !p.exists() {
                    fs::create_dir_all(p)?;
                }
            }
            let mut outfile = File::create(&outpath)?;
            io::copy(&mut file, &mut outfile)?;
        }
    }

    // 3. Clean up the zip file from disk
    fs::remove_file(zip_filename)?;
    println!("[RUST ASR] Extraction clean! Model ready for engine usage.");
    Ok(())
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    // Run the pre-flight check before spinning up the audio devices
    ensure_model_exists()?;

    let model = Model::new(Path::new(MODEL_DIR))
        .ok_or("Failed to initialize Vosk engine framework asset arrays.")?;
    
    let commands: Vec<&str> = vec![]; 
    let mut recognizer = if commands.is_empty() {
        Recognizer::new(&model, 16000.0)?
    } else {
        let grammar_json = format!("[\"{}\"]", commands.join("\",\""));
        Recognizer::new_grm(&model, 16000.0, &grammar_json)?
    };

    let (tx, rx) = unbounded::<Vec<i16>>();
    let _stream = audio::start_microphone_stream(tx)?;
    eprintln!("[RUST ASR] System fully armed. Listening...");

    for audio_buffer in rx {
        if recognizer.accept_waveform(&audio_buffer).is_final() {
            let filtered_phrase = recognizer.result().single().unwrap().text.trim().to_string();
            if !filtered_phrase.is_empty() {
                println!("{}", filtered_phrase);
                io::stdout().flush()?;
            }
        }
    }
    Ok(())
}
