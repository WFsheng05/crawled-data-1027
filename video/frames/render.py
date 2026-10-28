import os, subprocess, sys, time
sys.path.insert(0, r"C:\total workspace\Deepseek harness\one\bili_crawl\video3")
import frames7
from engine2 import FPS

HERE = r"C:\total workspace\Deepseek harness\one\bili_crawl\video3"
FRAMES = os.path.join(HERE, "fout8")
OUT = os.path.join(HERE, "bili_1028_final.mp4")
FF = r"C:\Users\Admin\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0.2-full_build\bin\ffmpeg.exe"

os.makedirs(FRAMES, exist_ok=True)
total = int(frames7.DUR * FPS)
t0 = time.time()
for i in range(total):
    frames7.render(i / FPS).save(os.path.join(FRAMES, f"f{i:05d}.png"), compress_level=0)
    if i % 300 == 0:
        print(f"  {i}/{total}  {time.time()-t0:.0f}s", flush=True)
print(f"帧完成 {total} / {time.time()-t0:.0f}s")

cmd = [FF, "-y", "-framerate", str(FPS), "-i", os.path.join(FRAMES, "f%05d.png"),
       "-c:v", "libx264", "-preset", "slow", "-crf", "18",
       "-pix_fmt", "yuv420p", "-movflags", "+faststart", OUT]
r = subprocess.run(cmd, capture_output=True, text=True)
if r.returncode != 0:
    print(r.stderr[-1200:], file=sys.stderr); sys.exit(1)
print(f"完成: {OUT} ({os.path.getsize(OUT)/1024/1024:.2f} MB)")
