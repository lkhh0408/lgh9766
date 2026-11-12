const { chromium } = require('playwright-core');
const D='/tmp/claude-0/-home-user-lgh9766/b52f1d6d-22f0-5bcd-a4bc-05ad7db7a50f/scratchpad/thumbs5/';
(async () => {
  const b = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell', args: ['--allow-file-access-from-files'] });
  for (const f of ['a1','a2','a3','a4','a5','a6','a7','a8','a9','a10','b1','b2','b3','b4','b5','b6','b7','b8','b9','b10']) {
    const p = await b.newPage({ viewport: { width: 1280, height: 720 } });
    await p.goto('file://'+D+f+'.html'); await p.evaluate(() => document.fonts.ready); await p.waitForTimeout(400);
    await p.screenshot({ path: D+f+'.png' });
  }
  await b.close();
})();
