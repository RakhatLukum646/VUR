# Privacy and Limitations

## Privacy

- Camera frames are processed for live gesture recognition and should be treated as sensitive biometric-adjacent data.
- The frontend does not persist captured frames locally.
- Auth sessions use HTTP-only cookies, while account and session metadata are stored in MongoDB.
- Email, password-reset, and session records must be protected with environment-specific secrets and production TLS.

## Product Limitations

- Recognition quality depends on hand size in frame, lighting, background contrast, and signer consistency.
- The classifier only covers the gestures present in the trained dataset and supported label set.
- Continuous sign language translation remains an approximation because the current pipeline is still gesture-sequence based rather than a full temporal language model.
- Translation quality can degrade when the upstream classifier emits ambiguous or unsupported signs.

## Recommended User Warnings

- Ask users to keep one hand centered and well lit.
- Tell users to pause briefly between words so the phrase boundary can be detected.
- Warn users when the system falls back to raw sign sequences instead of LLM-polished text.
