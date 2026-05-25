# PIWM Target Prompt-Ready Index

- records: 318
- video_backed_records: 118
- video_pending_records: 200
- prompt_records: 318

## Best Dialogue Act Counts

| Act | Count |
|---|---:|
| Elicit | 53 |
| Greet | 53 |
| Hold | 53 |
| Inform | 53 |
| Reassure | 53 |
| Recommend | 53 |

## Red Lines

- video_pending records are not multimodal training rows until Kling videos and sampled frames exist.
- promptready_index.jsonl is an upstream generation index, not an ms-swift SFT file.
- Only the existing 118 video-backed records can be imported into PIWM-Target-Frontcam-v1 today.
