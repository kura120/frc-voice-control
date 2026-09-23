use cpal::traits::{DeviceTrait, HostTrait, StreamTrait};
use crossbeam_channel::Sender;

pub struct AudioConfig {
    pub sample_rate: u32,
    pub channels: u16,
}

impl Default for AudioConfig {
    fn default() -> Self {
        Self { sample_rate: 16000, channels: 1 }
    }
}

pub fn start_microphone_stream(tx: Sender<Vec<i16>>) -> Result<cpal::Stream, Box<dyn std::error::Error>> {
    let host = cpal::default_host();
    let device = host.default_input_device().ok_or("Failed to locate default audio input device.")?;
    let config = AudioConfig::default();

    let stream_config = cpal::StreamConfig {
        channels: config.channels,
        sample_rate: cpal::SampleRate(config.sample_rate),
        buffer_size: cpal::BufferSize::Default,
    };

    let stream = device.build_input_stream(
        &stream_config,
        move |data: &[i16], _| { if !data.is_empty() { let _ = tx.send(data.to_vec()); } },

        |err| eprintln!("Audio stream error: {}", err),
        None,
    )?;

    stream.play()?;
    Ok(stream)
}
