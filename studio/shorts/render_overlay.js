const { chromium } = require('playwright-core');
const D='/tmp/claude-0/-home-user-lgh9766/b52f1d6d-22f0-5bcd-a4bc-05ad7db7a50f/scratchpad/shorts/';
(async () => {
  const b = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell', args: ['--allow-file-access-from-files'] });
  for (const f of ['01-03','01-09','01-20','02-02','02-12','02-16']) {
    const p = await b.newPage({ viewport: { width: 1080, height: 1920 } });
    await p.goto('file://'+D+'ov_'+f+'.html'); await p.evaluate(() => document.fonts.ready); await p.waitForTimeout(400);
    await p.screenshot({ path: D+'ov_'+f+'.png', omitBackground: true });
  }
  await b.close();
})();
