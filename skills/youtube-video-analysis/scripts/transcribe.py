#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11,<3.13"
# dependencies = ["faster-whisper==1.2.1", "av==18.1.0", "ctranslate2==4.8.2"]
# ///
"""默认转写入口：faster-whisper + 固定 medium 模型 + int8 量化（CPU）。

依赖里 av 必须钉在 19 以下：faster-whisper 1.2.1 调用的 av.open(metadata_errors=...)
在 av 19 被移除，不钉的话 uv 换一个 Python 版本解析就会在读音频时报 TypeError。

用法：
    uv run <skill-dir>/scripts/transcribe.py <audio> --out-dir <dir>

模型固定为 Systran/faster-whisper-medium，首次运行下载到 HuggingFace 缓存
（~/.cache/huggingface/hub），之后只读本地缓存、不再联网。
只有用户明确要求时才改 --model / --compute-type。
"""
import argparse
import json
import os
import pathlib
import time

from faster_whisper import WhisperModel

DEFAULT_MODEL = "medium"
DEFAULT_COMPUTE_TYPE = "int8"
ZH_PROMPT = "以下是普通话的句子，使用简体中文。"


def ts(seconds: float, sep: str) -> str:
    ms = int(round(seconds * 1000))
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d}{sep}{ms:03d}"


def load_model(name: str, compute_type: str, threads: int) -> WhisperModel:
    kwargs = dict(device="cpu", compute_type=compute_type, cpu_threads=threads)
    try:
        return WhisperModel(name, local_files_only=True, **kwargs)
    except Exception:
        print(f"[transcribe] 本地无 {name} 缓存，首次下载…", flush=True)
        return WhisperModel(name, **kwargs)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("audio")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--language", default="zh")
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--compute-type", default=DEFAULT_COMPUTE_TYPE)
    ap.add_argument("--beam-size", type=int, default=1)
    ap.add_argument("--initial-prompt", default=None)
    ap.add_argument("--threads", type=int, default=min(os.cpu_count() or 4, 8))
    args = ap.parse_args()

    audio = pathlib.Path(args.audio)
    out_dir = pathlib.Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    prompt = args.initial_prompt
    if prompt is None and args.language == "zh":
        prompt = ZH_PROMPT

    t0 = time.time()
    model = load_model(args.model, args.compute_type, args.threads)
    t_load = time.time() - t0

    segments, info = model.transcribe(
        str(audio),
        language=args.language,
        beam_size=args.beam_size,
        initial_prompt=prompt,
        vad_filter=True,
        condition_on_previous_text=False,
    )
    rows = []
    for seg in segments:
        text = seg.text.strip()
        if text:
            rows.append({"start": seg.start, "end": seg.end, "text": text})
    elapsed = time.time() - t0

    stem = audio.stem
    (out_dir / f"{stem}.txt").write_text("\n".join(r["text"] for r in rows) + "\n", encoding="utf-8")
    (out_dir / f"{stem}.srt").write_text(
        "".join(
            f"{i}\n{ts(r['start'], ',')} --> {ts(r['end'], ',')}\n{r['text']}\n\n"
            for i, r in enumerate(rows, 1)
        ),
        encoding="utf-8",
    )
    (out_dir / f"{stem}.vtt").write_text(
        "WEBVTT\n\n"
        + "".join(f"{ts(r['start'], '.')} --> {ts(r['end'], '.')}\n{r['text']}\n\n" for r in rows),
        encoding="utf-8",
    )
    meta = {
        "engine": "faster-whisper",
        "model": args.model,
        "compute_type": args.compute_type,
        "beam_size": args.beam_size,
        "language": info.language,
        "audio_seconds": round(info.duration, 1),
        "elapsed_seconds": round(elapsed, 1),
        "model_load_seconds": round(t_load, 1),
        "realtime_factor": round(info.duration / elapsed, 2) if elapsed else None,
        "segments": rows,
    }
    (out_dir / f"{stem}.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
    print(
        f"[transcribe] {args.model}/{args.compute_type} audio={info.duration:.0f}s "
        f"elapsed={elapsed:.0f}s speed={meta['realtime_factor']}x chars={sum(len(r['text']) for r in rows)} "
        f"-> {out_dir / (stem + '.txt')}",
        flush=True,
    )


if __name__ == "__main__":
    main()
