const CaptionMotion = (() => {
  const presets = {
    pop: {label:'Sorot + Pop', hint:'Kata aktif berwarna dan membesar sesaat.', mode:'highlight', animation:'pop'},
    elastic: {label:'Lentur', hint:'Kata aktif memendek lalu memantul kembali.', mode:'highlight', animation:'bounce'},
    karaoke: {label:'Karaoke', hint:'Warna mengisi kata mengikuti durasi ucapan.', mode:'karaoke', animation:'none'},
    typewriter: {label:'Muncul per kata', hint:'Kata muncul berurutan saat diucapkan.', mode:'line', animation:'typewriter'},
    word: {label:'Satu kata', hint:'Satu kata bergantian dengan efek pop.', mode:'word', animation:'pop'},
    plain: {label:'Tanpa gerak', hint:'Seluruh baris tetap terlihat.', mode:'line', animation:'none'},
    rise: {label:'Baris naik lembut',hint:'Seluruh baris masuk dari bawah secara bersamaan.',mode:'line',animation:'rise'},
    fade: {label:'Sorot memudar',hint:'Kata aktif muncul secara lembut.',mode:'highlight',animation:'fade'},
    zoom: {label:'Zoom kata',hint:'Kata aktif membesar ke ukuran normal.',mode:'highlight',animation:'zoom'},
    box: {label:'Kotak aktif',hint:'Satu kata disorot dalam kotak.',mode:'box',animation:'pop'},
    wordBounce: {label:'Satu kata memantul',hint:'Satu kata bergantian dengan pantulan.',mode:'word',animation:'bounce'},
    wordFade: {label:'Satu kata lembut',hint:'Satu kata bergantian dengan transisi lembut.',mode:'word',animation:'fade'},
  };
  function apply(rows, name, highlight = '#abff66') {
    const preset = presets[name]; if (!preset) return;
    rows.forEach(row => {
      row.style = {...row.style, mode:preset.mode, animation:preset.animation, highlight};
      (row.words || []).forEach(word => {if (word.style) {word.style = {...word.style}; delete word.style.animation;}});
    });
  }
  function picker(id, value = 'pop') {
    return `<label for="${id}">Animasi subtitle</label><select id="${id}">${Object.entries(presets).map(([key,p])=>`<option value="${key}" ${key===value?'selected':''}>${p.label}</option>`).join('')}</select>`;
  }
  function demo(host, select) {
    host.classList.add('motion-demo');
    host.innerHTML = '<div class="motion-stage"></div><div class="motion-demo-controls"><button type="button" class="ghost">Putar contoh</button><span>Contoh animasi · tanpa suara</span></div><p class="field-help"></p>';
    const frame=host.querySelector('.motion-stage'), button=host.querySelector('button'), hint=host.querySelector('p');
    const player=new EventTarget(); player.currentTime=0; player.paused=true;
    const cue={start:0,end:3.6,text:'Ini momen paling menarik',words:['Ini','momen','paling','menarik'].map((word,i)=>({word,start:i*.8,end:(i+1)*.8}))};
    const clip={captions:[cue],subtitle_position:'middle'};
    const overlay=SubtitleOverlay.mount(frame,player,()=>clip,0);
    let raf, started;
    function stop(){cancelAnimationFrame(raf);player.paused=true;button.textContent='Putar contoh';}
    function tick(now){
      if(!host.isConnected){stop();overlay.destroy();return;}
      player.currentTime=(now-started)/1000;overlay.paint();
      if(player.currentTime>=3.6){stop();player.currentTime=.25;overlay.paint();return;}
      raf=requestAnimationFrame(tick);
    }
    function refresh(){stop();apply([cue],select.value);cue.style.size=160;player.currentTime=.25;hint.textContent=presets[select.value]?.hint||'';overlay.paint();}
    select.addEventListener('change',refresh);
    button.onclick=()=>{if(!player.paused){stop();return;}player.paused=false;button.textContent='Jeda contoh';started=performance.now();raf=requestAnimationFrame(tick);};
    refresh();
    return {destroy(){stop();overlay.destroy();select.removeEventListener('change',refresh);}};
  }
  return {presets,apply,picker,demo};
})();
