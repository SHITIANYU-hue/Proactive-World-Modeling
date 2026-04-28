#!/usr/bin/env node
/**
 * Generate one PIWM video with Kling from a spec-compliant prompt.json.
 *
 * This tool only handles the Kling API call and video file write. The Python
 * data pipeline remains the source of truth for schema validation and JSONL
 * export. Frame extraction is intentionally left as a separate step so the
 * main data pipeline can stay free of media dependencies.
 */

import { access, copyFile, mkdir, readFile, writeFile } from 'node:fs/promises';
import { dirname, join } from 'node:path';

function parseArgs(argv) {
  const opts = {
    prompt: null,
    outRoot: 'Archive_generated',
    outSession: null,
    model: 'kling-v3.0-t2v',
    aspectRatio: '16:9',
    duration: null,
    mode: 'pro',
    sound: 'off',
    pollTimeoutMs: 600000,
    dryRun: false,
    overwrite: false,
  };
  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    if (arg === '--prompt') opts.prompt = argv[++i];
    else if (arg === '--out-root') opts.outRoot = argv[++i];
    else if (arg === '--out-session') opts.outSession = argv[++i];
    else if (arg === '--model') opts.model = argv[++i];
    else if (arg === '--aspect-ratio') opts.aspectRatio = argv[++i];
    else if (arg === '--duration') opts.duration = Number(argv[++i]);
    else if (arg === '--mode') opts.mode = argv[++i];
    else if (arg === '--sound') opts.sound = argv[++i];
    else if (arg === '--poll-timeout-ms') opts.pollTimeoutMs = Number(argv[++i]);
    else if (arg === '--dry-run') opts.dryRun = true;
    else if (arg === '--overwrite') opts.overwrite = true;
    else throw new Error(`Unknown argument: ${arg}`);
  }
  if (!opts.prompt) throw new Error('Missing --prompt path/to/prompt.json');
  return opts;
}

async function fileExists(path) {
  try {
    await access(path);
    return true;
  } catch {
    return false;
  }
}

function requireField(obj, path) {
  const parts = path.split('.');
  let current = obj;
  for (const part of parts) {
    if (current === null || typeof current !== 'object' || !(part in current)) {
      throw new Error(`prompt.json missing required field: ${path}`);
    }
    current = current[part];
  }
  return current;
}

function toBuffer(file) {
  if (file.uint8ArrayData) return Buffer.from(file.uint8ArrayData);
  if (file.base64Data) return Buffer.from(file.base64Data, 'base64');
  throw new Error('Video payload does not contain uint8ArrayData or base64Data.');
}

async function loadPrompt(path, requireGenerationPrompt) {
  const prompt = JSON.parse(await readFile(path, 'utf-8'));
  requireField(prompt, 'session_id');
  requireField(prompt, 'product_category');
  requireField(prompt, 'persona.type');
  requireField(prompt, 'aida_stage');
  requireField(prompt, 'target_cue');
  const klingPrompt = prompt.kling_prompt || prompt.behavior_description;
  if (!klingPrompt && requireGenerationPrompt) {
    throw new Error('prompt.json needs kling_prompt or behavior_description for Kling generation.');
  }
  return { prompt, klingPrompt: klingPrompt || '' };
}

async function generateVideoFile(opts, prompt, klingPrompt, outDir) {
  const { config: loadDotenv } = await import('dotenv');
  const { createKlingAI } = await import('@ai-sdk/klingai');
  const { experimental_generateVideo: generateVideo } = await import('ai');
  loadDotenv();

  const accessKey = process.env.KLINGAI_ACCESS_KEY;
  const secretKey = process.env.KLINGAI_SECRET_KEY;
  if (!accessKey || !secretKey) {
    throw new Error('Missing KLINGAI_ACCESS_KEY or KLINGAI_SECRET_KEY in environment.');
  }

  const klingai = createKlingAI({ accessKey, secretKey });
  const duration = opts.duration ?? Number(prompt.duration_seconds ?? 10);
  const { videos } = await generateVideo({
    model: klingai.video(opts.model),
    prompt: klingPrompt,
    aspectRatio: opts.aspectRatio,
    duration,
    providerOptions: {
      klingai: {
        mode: opts.mode,
        sound: opts.sound,
        pollTimeoutMs: opts.pollTimeoutMs,
      },
    },
  });
  if (!videos || videos.length === 0) throw new Error('No video returned by Kling.');
  const outputVideo = join(outDir, 'video.mp4');
  await writeFile(outputVideo, toBuffer(videos[0]));
  return outputVideo;
}

async function main() {
  const opts = parseArgs(process.argv.slice(2));
  const { prompt, klingPrompt } = await loadPrompt(opts.prompt, !opts.dryRun);
  const sessionId = opts.outSession || prompt.session_id;
  const outDir = join(opts.outRoot, sessionId);
  const videoPath = join(outDir, 'video.mp4');

  if ((await fileExists(videoPath)) && !opts.overwrite && !opts.dryRun) {
    throw new Error(`Output video already exists: ${videoPath}. Use --overwrite to replace it.`);
  }

  const plan = {
    session_id: sessionId,
    out_dir: outDir,
    video_path: videoPath,
    model: opts.model,
    aspect_ratio: opts.aspectRatio,
    duration: opts.duration ?? Number(prompt.duration_seconds ?? 10),
    mode: opts.mode,
    sound: opts.sound,
    prompt_chars: klingPrompt.length,
    dry_run: opts.dryRun,
  };

  if (opts.dryRun) {
    console.log(JSON.stringify(plan, null, 2));
    return;
  }

  await mkdir(outDir, { recursive: true });
  await copyFile(opts.prompt, join(outDir, 'prompt.json'));
  const outputVideo = await generateVideoFile(opts, prompt, klingPrompt, outDir);
  await writeFile(join(outDir, 'kling_generation.json'), JSON.stringify(plan, null, 2) + '\n', 'utf-8');
  console.log(JSON.stringify({ ...plan, video_path: outputVideo, success: true }, null, 2));
}

main().catch((error) => {
  console.error(error.stack || error.message);
  process.exit(1);
});
