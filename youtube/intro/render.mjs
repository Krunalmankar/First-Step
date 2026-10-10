// Renders intro.html frame by frame at 59.94 fps and encodes with ffmpeg.
// Usage: node render.mjs <out.mp4> [audio.wav]   |   node render.mjs --stills <dir> t1 t2 ...
import { createRequire } from 'module';
import { spawn } from 'child_process';
import path from 'path';
import fs from 'fs';
const require = createRequire(import.meta.url);
const { chromium } = require(process.env.PLAYWRIGHT_PATH || '/opt/node22/lib/node_modules/playwright');

const here = path.dirname(new URL(import.meta.url).pathname);
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
await page.goto('file://' + path.join(here, 'intro.html'));
await page.evaluate(() => window.ready);
await page.waitForTimeout(500);

const args = process.argv.slice(2);
if (args[0] === '--stills') {
  fs.mkdirSync(args[1], { recursive: true });
  for (const t of args.slice(2)) {
    await page.evaluate(t => window.render(t), +t);
    await page.screenshot({ path: path.join(args[1], `t${t}.png`) });
  }
} else {
  const [out, audio] = args;
  const FPS = 60000 / 1001, duration = await page.evaluate(() => window.DURATION);
  const frames = Math.round(duration * FPS);
  const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', '60000/1001', '-c:v', 'mjpeg', '-i', '-',
    ...(audio ? ['-i', audio, '-c:a', 'aac', '-b:a', '192k', '-ar', '48000', '-shortest'] : []),
    '-c:v', 'libx264', '-preset', 'slow', '-crf', '16', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', out], { stdio: ['pipe', 'inherit', 'inherit'] });
  for (let f = 0; f < frames; f++) {
    await page.evaluate(t => window.render(t), f / FPS);
    const buf = await page.screenshot({ type: 'jpeg', quality: 95 });
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
    if (f % 300 === 0) console.log(`frame ${f}/${frames}`);
  }
  ff.stdin.end();
  await new Promise(r => ff.on('close', r));
}
await browser.close();
