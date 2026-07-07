# Sample Audio Files

Place your test audio files here for evaluation and development.

## Included Files

| File | Description |
|------|-------------|
| `sample_tone.wav` | Synthetic 440 Hz sine wave (3 s) — used for unit tests |

## Recommended Test Files

For meaningful WER / ROUGE evaluation, add real speech recordings:

| File | Suggested Content | Duration |
|------|-------------------|----------|
| `sample_01.wav` | Clear single-speaker speech, quiet room | ~30 s |
| `sample_02.wav` | Speech with moderate background noise | ~60 s |
| `sample_03.wav` | Technical vocabulary (e.g. lecture) | ~120 s |
| `sample_04.wav` | Multi-speaker conversation | ~180 s |

## Supported Formats

`.wav`, `.mp3`, `.m4a`, `.ogg`, `.flac`, `.aac`

## Notes

- Whisper works best with **16 kHz mono WAV** files.
- For accurate WER evaluation, prepare a matching ground-truth transcript
  and paste it into the **Evaluation** tab of the GUI.
