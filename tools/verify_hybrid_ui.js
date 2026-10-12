// Real browser, isolated API and synthetic media. No account or paid-provider calls.
const {chromium} = require('playwright');
const {spawn} = require('child_process');
const fs = require('fs');
const path = require('path');
const assert = require('assert/strict');
const ROOT = path.resolve(__dirname,'..'), OUT=path.join(ROOT,'build','hybrid-browser');
const BASE='http://127.0.0.1:8768';
const wait = ms => new Promise(resolve=>setTimeout(resolve,ms));
async function main(){
  fs.mkdirSync(OUT,{recursive:true});
  const log=fs.openSync(path.join(OUT,'server.log'),'w');
  const server=spawn(path.join(ROOT,'.venv-build','Scripts','python.exe'),[path.join(__dirname,'serve_hybrid_fixture.py')],{cwd:ROOT,stdio:['ignore',log,log],windowsHide:true});
  let browser;
  const report={widths:[],checks:[],errors:[]};
  try{
    for(let i=0;i<100;i++){try{if((await fetch(BASE+'/api/health')).ok)break;}catch{}await wait(200);}
    const fixture=JSON.parse(fs.readFileSync(path.join(OUT,'fixture.json'),'utf8'));
    browser=await chromium.launch({headless:true,executablePath:'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe'});
    const page=await browser.newPage({viewport:{width:1440,height:1000}});
    page.on('pageerror',error=>report.errors.push(error.message));
    let encodes=0, metadataRequests=0;
    page.on('request',r=>{if(r.method()==='POST' && /\/clips\/\d+\/preview/.test(r.url()))encodes++;});
    page.on('request',r=>{if(r.url().endsWith('/api/link-info'))metadataRequests++;});
    await page.goto(BASE,{waitUntil:'networkidle'});
    await page.evaluate(()=>{const wizard=document.querySelector('#wizardOverlay');if(wizard)wizard.hidden=true;});
    await page.locator('#processingMode').selectOption('offline');
    assert.equal(await page.locator('#processingMode').inputValue(),'offline');
    await page.locator('#source').fill('https://youtu.be/abcdefghijk');
    await wait(1000);
    assert.equal(metadataRequests,0,'Offline form must not fetch URL metadata');
    await page.locator('#source').fill('');
    await page.locator('#detectLocalModel').click();
    await page.waitForFunction(()=>document.querySelector('#localModelStatus').textContent.includes('Runtime') || /model runtime tersedia/.test(document.querySelector('#localModelStatus').textContent));
    report.checks.push('offline selector; actual local-discovery error or available state');
    await page.route('**/api/ai/models',async route=>{await wait(300);await route.fulfill({json:{models:[{id:'fixture-old-model'}],recommended:'fixture-old-model'}});});
    await page.locator('#processingMode').selectOption('online_ai');
    assert.equal(await page.locator('#localLlmFields').isVisible(),false);
    await page.locator('#aiProvider').selectOption('openai');
    await page.locator('#aiKey').fill('fixture-placeholder');
    await page.locator('#aiDetect').click();
    await page.locator('#aiProvider').selectOption('groq');
    assert.equal(await page.locator('#aiKey').inputValue(),'');
    await wait(700);
    assert.equal(await page.locator('#aiModel').inputValue(),'auto');
    report.checks.push('provider switch clears key and ignores stale discovery; cloud discovery uses an explicit fixture');
    await page.locator('#processingMode').selectOption('hybrid');
    assert.equal(await page.locator('#localLlmFields').isVisible(),true);
    for(const width of [320,360,390,540,680,768,1024,1440]){
      await page.setViewportSize({width,height:950});
      const overflow=await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1);
      assert.equal(overflow,false,`Home overflow at ${width}`);report.widths.push(width);
    }
    await page.setViewportSize({width:1440,height:1000});
    await page.locator('#nav [data-page="projects"]').click();
    await page.locator(`[data-open="${fixture.project_id}"]`).click();
    await page.locator('#clipGrid [data-edit]').first().click();
    await page.locator('#tlVideo').waitFor();
    await page.waitForFunction(()=>document.querySelector('#tlVideo')?.readyState>=2);
    const box=await page.locator('#tlStage .output-frame').boundingBox();
    assert.ok(Math.abs(box.width/box.height-9/16)<.02,'Portrait frame ratio');
    await page.evaluate(()=>{const video=document.querySelector('#tlVideo');video.currentTime=1.5;});
    await wait(150);
    assert.match(await page.locator('.live-subtitle').innerText(),/Halo.*dunia/);
    const early=await page.locator('.live-subtitle span').first().evaluate(el=>getComputedStyle(el).color);
    await page.evaluate(()=>{document.querySelector('#tlVideo').currentTime=3;});await wait(150);
    const late=await page.locator('.live-subtitle span').first().evaluate(el=>getComputedStyle(el).color);
    assert.notEqual(early,late,'Active word updates after seek');
    await page.locator('[data-inspector="clip"]').click();
    for(const canvas of ['square','landscape','portrait']){
      await page.locator('#tlCanvas').selectOption(canvas);await wait(250);
      const frame=await page.locator('#tlStage .output-frame').boundingBox();
      const ratio={square:1,landscape:16/9,portrait:9/16}[canvas];
      assert.ok(Math.abs(frame.width/frame.height-ratio)<.03,canvas);
    }
    assert.equal(encodes,0,'Ordinary editor changes must not encode');
    report.checks.push('portrait/square/landscape; live words and seek; zero automatic encoded previews');
    for(const width of [360,540,768,1024,1440]){
      await page.setViewportSize({width,height:950});
      const overflow=await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1);
      assert.equal(overflow,false,`Editor overflow at ${width}`);
    }
    await page.setViewportSize({width:1440,height:1000});
    await page.screenshot({path:path.join(OUT,'editor.png')});
    await page.keyboard.press('Escape');
    await page.locator('[data-tl="close"]').click().catch(()=>{});
    await page.locator('#nav [data-page="home"]').click();
    await page.locator('#processingMode').focus();await page.keyboard.press('ArrowDown');
    assert.equal(await page.locator('#processingMode').evaluate(el=>el===document.activeElement),true);
    report.checks.push('keyboard select focus');
    await page.screenshot({path:path.join(OUT,'home.png')});
    assert.deepEqual(report.errors,[]);
    report.success=true;
  }finally{
    if(browser)await browser.close();server.kill();fs.closeSync(log);
    fs.writeFileSync(path.join(OUT,'results.json'),JSON.stringify(report,null,2));
  }
  console.log(JSON.stringify(report));
}
main().catch(error=>{console.error(error);process.exitCode=1;});
