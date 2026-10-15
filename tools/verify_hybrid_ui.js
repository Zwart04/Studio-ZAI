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
    assert.equal(await page.locator('#subPos').isVisible(),true,'Subtitle position visible without expanding');
    assert.equal(await page.locator('#analysisMode').isVisible(),true,'Analysis visible without expanding');
    assert.equal(await page.locator('#advDetails').evaluate(el=>el.tagName),'SECTION');
    assert.equal(await page.locator('#transcriptSettings #asrSpeed').count(),1);
    assert.equal(await page.locator('#ggufModel').isVisible(),true,'GGUF controls not collapsed');
    await page.route('**/api/local-llm/stop', async route=>{await wait(250); await route.fulfill({json:{stopped:true}});});
    await page.locator('#stopGguf').click();
    assert.equal(await page.locator('#stopGguf').getAttribute('aria-busy'),'true');
    assert.equal(await page.locator('#stopGguf').isDisabled(),true);
    await page.locator('#stopGguf:not([aria-busy])').waitFor();
    assert.match(await page.locator('#stopGguf').innerText(),/Lepaskan/);
    for(const id of ['loadGguf','stopGguf']) assert.ok((await page.locator('#'+id).boundingBox()).height>=44);
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
    await page.unroute('**/api/ai/models');
    await page.route('**/api/ai/models',route=>route.fulfill({json:{models:[{id:'gpt-6-luna',label:'GPT Luna',price:{input:.1,output:.5,checked:'2026-10-14'}},{id:'gpt-6-astra',label:'GPT Astra'}],recommended:'gpt-6-luna',guidance:{recommended:'gpt-6-luna',cheapest:'gpt-6-luna',smartest:'gpt-6-astra',note:'Fixture guidance'}}}));
    await page.locator('#aiProvider').selectOption('openai');
    await page.locator('#aiKey').fill('fixture-placeholder');
    await page.locator('#aiDetect').click();
    await page.locator('#aiModelPriority:enabled').waitFor();
    await page.locator('#aiModelPriority').selectOption('smartest');
    assert.equal(await page.locator('#aiModel').inputValue(),'gpt-6-astra');
    await page.locator('#aiModelPriority').selectOption('cheapest');
    assert.equal(await page.locator('#aiModel').inputValue(),'gpt-6-luna');
    assert.match(await page.locator('#aiModelDetail').innerText(),/0.1/);
    for(const provider of ['openai','anthropic','gemini','groq','deepseek']) {
      await page.locator('#aiProvider').selectOption(provider);
      await page.waitForFunction(()=>document.querySelector('#providerLogo')?.naturalWidth>0);
      assert.ok((await page.locator('#providerHelp a').first().getAttribute('href')).startsWith('https://'));
    }
    await page.locator('#aiProvider').selectOption('gemini');
    assert.match(await page.locator('#providerHelp').innerText(),/gratis/);
    assert.equal(await page.locator('#aiModelPriority').isDisabled(),true);
    assert.equal(await page.locator('[data-provider-pick]').count(),0);
    report.checks.push('provider and model dropdowns, official local icons, API help links, free quota badge, model priorities and stale-provider reset');

    await page.screenshot({path:path.join(OUT,'model-dropdowns.png')});
    await page.locator('#processingMode').selectOption('local');
    assert.equal(await page.locator('#localLlmFields').isVisible(),true);
    assert.equal(await page.locator('#processingMode option[value="hybrid"]').count(),0);
    assert.equal(await page.locator('[name=creationTask][value=transcript]').count(),0);
    for (const preset of ['portrait','square','classic','letterbox','landscape','original']) {
      await page.locator(`[name=canvasPreset][value=${preset}]`).check();
      assert.equal(await page.locator('#canvasSize').inputValue(),preset==='letterbox'?'portrait':preset);
      assert.equal(await page.locator('#frameFit').inputValue(),['letterbox','original'].includes(preset)?'fit':'center');
    }
    await page.locator('[name=canvasPreset][value=portrait]').check();
    report.checks.push('clip-only workflow, no Hybrid option, six canvas choices with crop/fit mapping');
    for(const width of [320,360,390,540,680,768,1024,1440]){
      await page.setViewportSize({width,height:950});
      const overflow=await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1);
      assert.equal(overflow,false,`Home overflow at ${width}`);report.widths.push(width);
    }
    await page.setViewportSize({width:1440,height:1000});
    await page.screenshot({path:path.join(OUT,'home-redesign.png'),fullPage:true});
    await page.locator('#homeCaptionMotion').selectOption('elastic');
    await page.locator('#homeMotionDemo button').click();
    await wait(90);
    assert.match(await page.locator('#homeMotionDemo button').innerText(),/Jeda/);
    await page.locator('#homeMotionDemo button').click();
    await page.locator('#homeCaptionMotion').selectOption('pop');
    report.checks.push('motion demo starts, pauses, and switches preset');
    assert.equal(await page.locator('#homeProjects .home-clip').count(),3);
    assert.match(await page.locator('#homeProjects').innerText(),/Halo/);
    await page.locator('#nav [data-page="projects"]').click();
    await page.locator(`[data-open="${fixture.project_id}"]`).click();
    const card=await page.locator('#clipGrid .clip-open').first().boundingBox();
    assert.ok(Math.abs(card.width/card.height-9/16)<.02,'Portrait card ratio');
    for (const [index,ratio] of [[1,16/9],[2,1]]) {
      const frame=await page.locator('#clipGrid .clip-open').nth(index).boundingBox();
      assert.ok(Math.abs(frame.width/frame.height-ratio)<.02,'Preview card canvas ratio');
    }
    assert.match(await page.locator('#clipGrid .potential-score').nth(1).innerText(),/90/);
    await page.waitForFunction(()=>document.querySelector('#clipGrid img.thumb')?.naturalWidth>0);
    for (const width of [360,540,768,1024,1440]) {
      await page.setViewportSize({width,height:1000});
      assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1),false,`Card overflow at ${width}`);
    }
    await page.screenshot({path:path.join(OUT,'preview-cards.png')});
    await page.locator('#clipGrid .potential-score').first().waitFor();
    report.checks.push('portrait preview card and visible score badge');
    await page.locator('#clipGrid [data-edit]').first().click();
    await page.locator('#tlVideo').waitFor();
    await page.locator('[data-category="Semua"]').click();
    assert.ok(await page.locator('[data-preset]').count()>=24,'Template catalog must load successfully');
    await page.waitForFunction(()=>document.querySelector('#tlVideo')?.readyState>=2);
    const box=await page.locator('#tlStage .output-frame').boundingBox();
    assert.ok(Math.abs(box.width/box.height-9/16)<.02,'Portrait frame ratio');
    await page.evaluate(()=>{const video=document.querySelector('#tlVideo');video.currentTime=Number(video.dataset.sourceStart)+.5;window.originalPlayer=video;});
    await wait(150);
    assert.match(await page.locator('#tlStage .live-subtitle').innerText(),/Halo.*dunia/);
    const early=await page.locator('#tlStage .live-subtitle span').first().evaluate(el=>getComputedStyle(el).color);
    await page.evaluate(()=>{const video=document.querySelector('#tlVideo');video.currentTime=Number(video.dataset.sourceStart)+2;});await wait(150);
    const late=await page.locator('#tlStage .live-subtitle span').first().evaluate(el=>getComputedStyle(el).color);
    assert.notEqual(early,late,'Active word updates after seek');
    await page.locator('[data-inspector="subtitles"]').click();
    const originalTiming=await page.locator('#tlCaptions').inputValue();
    for(const motion of ['pop','elastic','karaoke','typewriter','word','plain','rise','fade','zoom','box','wordBounce','wordFade']) {
      await page.locator('#tlCaptionMotion').selectOption(motion);
      await page.locator('#tlApplyMotion').click();
      await page.evaluate(()=>{document.querySelector('#tlVideo').currentTime=1.25;});
      await wait(80);
      assert.ok(await page.locator('#tlStage .live-subtitle span').count()>0);
      assert.equal(await page.locator('#tlCaptions').inputValue(),originalTiming);
    }
    report.checks.push('twelve motion presets preserve actual clip text and timestamps');
    await page.locator('[data-inspector="clip"]').click();
    for(const canvas of ['square','classic','landscape','portrait']){
      await page.locator('#tlCanvas').selectOption(canvas);await wait(250);
      const frame=await page.locator('#tlStage .output-frame').boundingBox();
      const ratio={square:1,classic:4/3,landscape:16/9,portrait:9/16}[canvas];
      assert.ok(Math.abs(frame.width/frame.height-ratio)<.03,canvas);
    }
    assert.equal(encodes,0,'Ordinary editor changes must not encode');
    report.checks.push('portrait/square/landscape; live words and seek; zero automatic encoded previews');
    assert.equal(await page.evaluate(()=>window.originalPlayer===document.querySelector('#tlVideo')),true,'Canvas changes retain video element');
    await page.locator('[data-inspector="subtitles"]').click();
    await page.locator('[data-category="Editorial"]').click();
    await page.locator('[data-preset="handwritten"]').click();
    await page.evaluate(()=>{const v=document.querySelector('#tlVideo');v.currentTime=Number(v.dataset.sourceStart)+.5;});await wait(100);
    assert.match(await page.locator('#tlStage .live-subtitle').first().evaluate(el=>getComputedStyle(el).fontFamily),/Kalam/);
    await page.locator('[data-cue-text="0"]').fill('Ucapan yang sudah diedit');await wait(100);
    assert.match(await page.locator('#tlStage .live-subtitle').first().innerText(),/Ucapan/);
    await page.locator('[data-tl="add-text"]').click();
    await page.locator('#tlText').fill('Overlay langsung');
    await page.locator('#tlLiveFont').selectOption('Anton');await wait(400);
    assert.match(await page.locator('#tlStage').innerText(),/Overlay langsung/);
    assert.equal(await page.evaluate(()=>window.originalPlayer===document.querySelector('#tlVideo')),true,'Adding text retains video element');
    assert.equal(encodes,0);
    report.checks.push('template font, editable transcript and added text update live without replacing or encoding the player');
    await page.locator('[data-inspector="clip"]').click();
    for(const mode of ['manual','split','blur','center']){
      await page.locator('#tlCrop').selectOption(mode);await wait(150);
      assert.equal(await page.evaluate(()=>window.originalPlayer===document.querySelector('#tlVideo')),true,'Framing retains decoder');
      if(mode!=='center')assert.equal(await page.locator('.live-framing').isVisible(),true);
    }
    const chooserPromise=page.waitForEvent('filechooser');
    await page.locator('[data-tl="add-media"]').click();
    const chooser=await chooserPromise;
    await chooser.setFiles({name:'overlay.png',mimeType:'image/png',buffer:Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+a5hsAAAAASUVORK5CYII=','base64')});
    await page.waitForFunction(()=>document.querySelector('img.live-timeline-asset')?.naturalWidth>0);
    assert.equal(await page.evaluate(()=>window.originalPlayer===document.querySelector('#tlVideo')),true,'Adding media retains decoder');
    report.checks.push('manual crop, split and blur draw live; uploaded image appears without video reload');
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
