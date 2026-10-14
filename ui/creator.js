/* Shared source/word/keyframe tools for the desktop editor. */
const CreatorEditor = (() => {
  const fonts = ['Inter','Anton','Barlow Condensed','DM Serif Display','Kalam'];
  const languages = {id:'Indonesia',en:'English',es:'Español',fr:'Français',de:'Deutsch',pt:'Português',ar:'العربية',ja:'日本語',ko:'한국어',zh:'中文',ru:'Русский'};
  const copy = value => JSON.parse(JSON.stringify(value));
  const clamp = (v,a,b) => Math.max(a,Math.min(b,v));
  function shiftFraming(data,offset,duration) {
    if(data?.top||data?.bottom)return {...data,...Object.fromEntries(['top','bottom'].filter(k=>data[k]).map(k=>[k,shiftFraming(data[k],offset,duration)]))};
    const f=copy(data||{}),frames=f.keyframes||[];if(!frames.length)return f;
    if(frames[0].time>0)frames.unshift({time:0,x:f.x??.5,y:f.y??.5});
    const at=time=>{let a=frames[0];for(const b of frames.slice(1)){if(time<=b.time){const r=clamp((time-a.time)/Math.max(.001,b.time-a.time),0,1);return {x:a.x+(b.x-a.x)*r,y:a.y+(b.y-a.y)*r};}a=b;}return {x:a.x,y:a.y};};
    const first=at(offset),last=at(offset+duration);return {...f,...first,keyframes:[{time:0,...first},...frames.filter(k=>k.time>offset&&k.time<offset+duration).map(k=>({...k,time:k.time-offset})),{time:duration,...last}]};
  }
  function dialog(title, body) {
    const el = document.createElement('dialog'); el.className = 'creator-dialog';
    el.innerHTML = `<header><div><span class="eyebrow">STUDIO ZAI / CREATOR</span><h2>${title}</h2></div><button data-close aria-label="Tutup">×</button></header>${body}`;
    document.body.append(el); el.showModal();
    const close = () => {el.querySelectorAll('video').forEach(v=>v.pause());el.close();el.remove();};
    el.querySelector('[data-close]').onclick = close;
    el.addEventListener('cancel',e=>{e.preventDefault();close();});
    return {el,close};
  }
  async function wait(job, status) {
    while (true) {
      const current = await api(`/api/jobs/${job.id}`);
      status.textContent = `${current.message || current.stage || 'Memproses'} · ${Math.round(current.progress || 0)}%`;
      if (current.status === 'done') return current.result;
      if (['error','cancelled'].includes(current.status)) throw new Error(current.error || current.message || 'Proses berhenti');
      await new Promise(r=>setTimeout(r,600));
    }
  }
  function wordRows(row) {
    if (!row.words?.length) {
      row.timing_quality = 'estimated';
      const words = row.text.trim().split(/\s+/).filter(Boolean), span=(row.end-row.start)/Math.max(1,words.length);
      row.words = words.map((word,i)=>({word,start:row.start+i*span,end:row.start+(i+1)*span}));
    }
    return row.words;
  }
  function words(editor) {
    let rows = copy(editor.clip.captions || []), index=0, selected=-1; const chosen=new Set();
    const variants=copy(editor.clip.caption_variants || {});
    let language=editor.clip.caption_language || state.project.language || 'id';
    variants[language]=copy(rows);
    const original = copy(rows);
    const {el,close} = dialog('Caption per kata', `<p class="field-help">Pilih baris lalu kata. Timing kata dari caption tanpa timestamp dan hasil terjemahan diperkirakan; bisa dikoreksi di sini.</p>
      <label>Versi subtitle tersimpan<select id="captionLanguage"></select></label><div class="creator-layout"><aside><select id="cueList" size="10" aria-label="Baris caption"></select></aside><section>
      <div id="wordPreview" class="word-preview"></div><div id="wordButtons" class="word-buttons"></div>
      <label>Tampilan caption<select id="captionMode"><option value="line">Seluruh baris</option><option value="word">Satu kata bergantian</option><option value="highlight">Highlight kata aktif</option><option value="box">Kotak kata aktif</option></select></label><div class="grid-2"><label>Warna highlight<input id="activeColor" type="color" value="#abff66"></label><label>Warna kotak<input id="boxColor" type="color" value="#111111"></label></div><label><input id="multiWords" type="checkbox"> Pilih beberapa kata</label><button id="selectWords" class="ghost">Pilih semua kata pada baris</button><label>Teks<input id="wordText"></label><div class="grid-2"><label>Mulai<input id="wordStart" type="number" step="0.01"></label><label>Selesai<input id="wordEnd" type="number" step="0.01"></label></div>
      <div class="grid-2"><label>Font<select id="wordFont">${fonts.map(f=>`<option>${f}</option>`).join('')}</select></label><label>Ukuran<input id="wordSize" type="number" min="14" max="160" value="56"></label><label>Warna<input id="wordColor" type="color" value="#ffffff"></label><label>Animasi<select id="wordAnimation">${['none','pop','bounce','fade','rise','zoom','typewriter'].map(a=>`<option>${a}</option>`).join('')}</select></label></div>
      <label><input id="wordBold" type="checkbox"> Tebal</label><div class="grid-2"><label>Posisi X (%)<input id="captionX" type="number" min="5" max="95"></label><label>Posisi Y (%)<input id="captionY" type="number" min="5" max="95"></label></div>
      <button id="applyStyle" class="ghost">Terapkan gaya baris ke semua caption</button></section></div>
      <details><summary>Terjemahan lokal & subtitle terpisah</summary><p class="field-help">Model bahasa diunduh saat pertama digunakan. Setelah itu terjemahan berjalan lokal. SRT/VTT dapat diunduh tanpa render video. Gaya per kata perlu disesuaikan karena susunan kata berubah.</p><div class="grid-2">${['Source','Target'].map((kind)=>`<label>${kind==='Source'?'Dari':'Ke'}<select id="translate${kind}">${Object.entries(languages).map(([id,label])=>`<option value="${id}">${label}</option>`).join('')}</select></label>`).join('')}</div><div class="row"><button id="translateCaptions">Unduh model & terjemahkan</button><button id="restoreCaptions">Pulihkan teks awal</button></div><div id="translatedFiles"></div></details>
      <button id="previewWords" class="ghost">Pratinjau video dengan perubahan ini</button><video id="captionVideo" controls playsinline hidden class="caption-video"></video><p id="creatorStatus" role="status"></p><footer><button id="applyWords" class="primary">Simpan caption</button></footer>`);
    const $c = id=>el.querySelector('#'+id), status=$c('creatorStatus');
    $c('captionMode').append(new Option('Karaoke fill', 'karaoke'));
    $c('translateSource').value=languages[language]?language:(state.project.transcript?.language||'id');$c('translateTarget').value='en';
    function list() { $c('cueList').innerHTML=rows.map((r,i)=>`<option value="${i}">${i+1}. ${escapeHtml(r.text)}</option>`).join('');$c('cueList').value=String(index);$c('captionLanguage').innerHTML=Object.keys(variants).map(id=>`<option value="${escapeHtml(id)}">${escapeHtml(languages[id]||id)}</option>`).join('');$c('captionLanguage').value=language; }
    $c('captionLanguage').onchange=()=>{variants[language]=copy(rows);language=$c('captionLanguage').value;rows=copy(variants[language]);index=0;selected=-1;chosen.clear();$c('translateSource').value=languages[language]?language:(state.project.transcript?.language||'id');list();paint();};
    function current() { const row=rows[index];return row ? (selected<0?row:wordRows(row)[selected]) : null; }
    function preview() {
      const row=rows[index];
      $c('wordPreview').innerHTML = row ? wordRows(row).map(w=>{const s={...row.style,...w.style};return `<span style="font-family:'${fonts.includes(s.font)?s.font:'Inter'}';font-size:${clamp(Number(s.size)||56,14,160)/2}px;color:${/^#[\da-f]{6}$/i.test(s.color)?s.color:'#ffffff'};font-weight:${s.bold?700:400}">${escapeHtml(w.word)}</span>`;}).join(' ') : 'Buat subtitle otomatis terlebih dahulu.';
    }
    function paint() {
      const row=rows[index], item=current(); if(!row||!item){preview();return;}
      $c('wordButtons').innerHTML=`<button data-word="-1" class="${selected<0?'active':''}">Seluruh baris</button>`+wordRows(row).map((w,i)=>`<button data-word="${i}" class="${selected===i||chosen.has(i)?'active':''}">${escapeHtml(w.word)}</button>`).join('');
      $c('wordButtons').querySelectorAll('button').forEach(b=>b.onclick=()=>{const next=+b.dataset.word;if(next<0||!$c('multiWords').checked)chosen.clear();if(next>=0){if(chosen.has(next)&&$c('multiWords').checked)chosen.delete(next);else chosen.add(next);}selected=next;paint();});
      const s={...row.style,...item.style};$c('captionMode').value=row.style?.mode||'line';$c('activeColor').value=row.style?.highlight||'#abff66';$c('boxColor').value=row.style?.boxColor||'#111111';
      $c('wordText').value=selected<0?item.text:item.word;$c('wordStart').value=item.start;$c('wordEnd').value=item.end;
      $c('wordFont').value=s.font||'Inter';$c('wordSize').value=s.size||56;$c('wordColor').value=s.color||'#ffffff';$c('wordBold').checked=!!s.bold;$c('wordAnimation').value=s.animation||'none';
      $c('captionX').value=Math.round((row.style?.x??.5)*100);$c('captionY').value=Math.round((row.style?.y??.82)*100);preview();
    }
    $c('cueList').onchange=()=>{index=+$c('cueList').value;selected=-1;chosen.clear();chosen.clear();paint();};
    ['wordFont','wordSize','wordColor','wordBold','wordAnimation','captionX','captionY'].forEach(id=>$c(id).oninput=()=>{
      const item=current(),row=rows[index];if(!item)return;
      item.style={...(item.style||{}),font:$c('wordFont').value,size:clamp(+$c('wordSize').value,14,160),color:$c('wordColor').value,bold:$c('wordBold').checked,animation:$c('wordAnimation').value};
      if(chosen.size>1)chosen.forEach(i=>wordRows(row)[i].style=copy(item.style));
      row.style={...row.style,x:clamp(+$c('captionX').value/100,.05,.95),y:clamp(+$c('captionY').value/100,.05,.95)};preview();
    });
    ['wordText','wordStart','wordEnd'].forEach(id=>$c(id).onchange=()=>{
      const item=current(),row=rows[index];if(!item)return;
      item.start=clamp(+$c('wordStart').value,selected<0?0:row.start,selected<0?editor.duration():row.end-.01);
      item.end=clamp(+$c('wordEnd').value,item.start+.01,selected<0?editor.duration():row.end);
      if(selected<0){item.text=$c('wordText').value;item.words=[];wordRows(item);}else{item.word=$c('wordText').value;row.text=row.words.map(w=>w.word).join(' ');}
      list();paint();
    });
    $c('selectWords').onclick=()=>{chosen.clear();wordRows(rows[index]).forEach((w,i)=>chosen.add(i));$c('multiWords').checked=true;selected=chosen.size?0:-1;paint();};
    ['captionMode','activeColor','boxColor'].forEach(id=>$c(id).oninput=()=>{const row=rows[index];if(row){row.style={...row.style,mode:$c('captionMode').value,highlight:$c('activeColor').value,boxColor:$c('boxColor').value};preview();}});
    $c('applyStyle').onclick=()=>{const item=current();if(!item)return;rows.forEach(r=>r.style=copy({...rows[index].style,...item.style}));selected=-1;chosen.clear();paint();};
    $c('restoreCaptions').onclick=()=>{language=editor.clip.caption_language || state.project.language || 'id';rows=copy(original);$c('translateSource').value=languages[language]?language:(state.project.transcript?.language||'id');index=0;selected=-1;chosen.clear();list();paint();};
    $c('translateCaptions').onclick=async()=>{
      const button=$c('translateCaptions');button.disabled=true;$c('applyWords').disabled=true;
      try{const job=await api(`/api/projects/${state.project.id}/translate`,{method:'POST',body:JSON.stringify({captions:rows,source:$c('translateSource').value,target:$c('translateTarget').value})});
        const result=await wait(job,status);if(!el.isConnected)return;variants[language]=copy(rows);language=$c('translateTarget').value;$c('translateSource').value=languages[language]?language:(state.project.transcript?.language||'id');rows=result.captions;index=0;variants[language]=copy(rows);selected=-1;chosen.clear();list();paint();
        $c('translatedFiles').innerHTML=['srt','vtt','ass'].map(ext=>`<a href="${mediaUrl(result.files[ext])}" download>Unduh ${ext.toUpperCase()}</a>`).join(' · ');
        status.textContent='Terjemahan siap. Simpan caption untuk menerapkannya pada video.';
      }catch(error){status.textContent=error.message;}finally{button.disabled=false;$c('applyWords').disabled=false;}
    };
    $c('previewWords').onclick=async()=>{const b=$c('previewWords');b.disabled=true;try{const job=await api(`/api/projects/${state.project.id}/clips/${editor.clip.index}/preview`,{method:'POST',body:JSON.stringify({captions:rows,timeline:editor.timeline})});const result=await wait(job,status);if(el.isConnected){$c('captionVideo').src=mediaUrl(result.mp4);$c('captionVideo').hidden=false;status.textContent='Pratinjau sesuai jalur ekspor. Tekan Simpan caption untuk menerapkan.';}}catch(e){status.textContent=e.message;}finally{b.disabled=false;}};
    $c('applyWords').onclick=async()=>{try{variants[language]=copy(rows);editor.clip.captions=rows;editor.clip.caption_variants=variants;editor.clip.caption_language=language;await editor.save(true);editor.renderInspector();editor.schedulePreview();close();}catch(error){status.textContent=error.message;}};
    list();paint();
  }
  function crop(editor, part=null) {
    const base=editor.items('video')[0];if(!base)return;
    let framing=copy((part ? base.framing?.[part] : base.framing) || {x:.5,y:.5,zoom:1,keyframes:[]});framing.keyframes ||= [];
    const sw=state.project.width||1920,sh=state.project.height||1080,ratios={portrait:9/16,square:1,classic:4/3,landscape:16/9,original:sw/sh};
    // Mode online: video penuh mungkin belum ada — pakai mp4 pratinjau terakhir bila ada.
    const previewSrc=editor.previewPath||state.project.source,previewBase=editor.previewPath?0:editor.clip.start;
    const {el,close}=dialog(part ? `Split gaming · ${part==='top'?'Facecam':'Gameplay'}` : 'Crop & keyframe',`<p class="field-help">Seret kotak pada video sumber. Tambahkan keyframe untuk mengikuti subjek. Waktu dihitung dari awal klip.</p><div class="crop-stage">${previewSrc?`<video muted playsinline preload="metadata" src="${mediaUrl(previewSrc)}"></video>`:`<p class="field-help crop-empty-note">Belum ada gambar. Tutup dialog ini, tekan Pratinjau di editor, lalu buka lagi.</p>`}<div class="crop-box" tabindex="0" role="slider" aria-label="Posisi crop"></div></div><div class="grid-2"><label>Waktu (detik)<input id="cropTime" type="number" step="0.1" min="0" max="${editor.duration()}" value="0"></label><label>Zoom<input id="cropZoom" type="range" min="1" max="4" step=".05" value="${framing.zoom}"></label></div><div class="grid-2"><label>X (%)<input id="cropX" type="number" min="0" max="100"></label><label>Y (%)<input id="cropY" type="number" min="0" max="100"></label></div><div class="row"><button id="addKey">＋ Keyframe di waktu ini</button><button id="followFace">Ikuti wajah otomatis</button><button id="clearKeys">Hapus keyframe</button></div><p class="field-help">Pelacakan memilih wajah terdekat dengan posisi awal. Periksa hasil saat ada beberapa orang.</p><div id="cropKeys" class="word-buttons"></div><p id="creatorStatus" role="status"></p><footer><button id="applyCrop" class="primary">Simpan crop</button></footer>`);
    const $c=id=>el.querySelector('#'+id),video=el.querySelector('video'),box=el.querySelector('.crop-box'),stage=el.querySelector('.crop-stage');
    stage.style.aspectRatio=`${sw}/${sh}`;if(video)video.onloadedmetadata=()=>video.currentTime=previewBase;
    function paint(){const ratio=part ? (9/16)/(part==='top'?(base.framing?.fraction||.35):1-(base.framing?.fraction||.35)) : (ratios[base.canvas]||9/16),w=Math.min(sw,sh*ratio)/framing.zoom/sw,h=Math.min(sh,sw/ratio)/framing.zoom/sh;
      box.style.cssText=`width:${w*100}%;height:${h*100}%;left:${clamp(framing.x-w/2,0,1-w)*100}%;top:${clamp(framing.y-h/2,0,1-h)*100}%`;
      $c('cropX').value=Math.round(framing.x*100);$c('cropY').value=Math.round(framing.y*100);
      $c('cropKeys').innerHTML=framing.keyframes.map((k,i)=>`<button data-key="${i}">${k.time.toFixed(1)}s <span data-delete="${i}" aria-label="Hapus keyframe">×</span></button>`).join('');
      $c('cropKeys').querySelectorAll('[data-key]').forEach(b=>b.onclick=e=>{const i=+b.dataset.key;if(e.target.dataset.delete!==undefined){framing.keyframes.splice(i,1);}else{const k=framing.keyframes[i];framing.x=k.x;framing.y=k.y;$c('cropTime').value=k.time;if(video)video.currentTime=previewBase+k.time;}paint();});
    }
    stage.onpointerdown=e=>{stage.setPointerCapture(e.pointerId);move(e);};stage.onpointermove=e=>{if(stage.hasPointerCapture(e.pointerId))move(e);};
    function move(e){const r=stage.getBoundingClientRect();framing.x=clamp((e.clientX-r.left)/r.width,0,1);framing.y=clamp((e.clientY-r.top)/r.height,0,1);paint();}
    box.onkeydown=e=>{const d={ArrowLeft:[-.01,0],ArrowRight:[.01,0],ArrowUp:[0,-.01],ArrowDown:[0,.01]}[e.key];if(d){e.preventDefault();framing.x=clamp(framing.x+d[0],0,1);framing.y=clamp(framing.y+d[1],0,1);paint();}};
    $c('cropZoom').oninput=()=>{framing.zoom=+$c('cropZoom').value;paint();};
    ['cropX','cropY'].forEach((id,i)=>$c(id).oninput=()=>{framing[i?'y':'x']=clamp(+$c(id).value/100,0,1);paint();});
    $c('cropTime').onchange=()=>{if(video)video.currentTime=previewBase+clamp(+$c('cropTime').value,0,editor.duration());};
    $c('addKey').onclick=()=>{const time=clamp(+$c('cropTime').value,0,editor.duration());framing.keyframes=framing.keyframes.filter(k=>Math.abs(k.time-time)>.01);framing.keyframes.push({time,x:framing.x,y:framing.y});framing.keyframes.sort((a,b)=>a.time-b.time);paint();};
    $c('clearKeys').onclick=()=>{framing.keyframes=[];paint();};
    $c('followFace').onclick=async()=>{const b=$c('followFace');b.disabled=true;try{const job=await api(`/api/projects/${state.project.id}/track-face`,{method:'POST',body:JSON.stringify({start:editor.clip.start,end:editor.clip.end,x:framing.x,y:framing.y})});const result=await wait(job,$c('creatorStatus'));if(!el.isConnected)return;framing={...result,zoom:framing.zoom};paint();$c('creatorStatus').textContent=`${result.detector}: ${result.detected_frames}/${result.sampled_frames} sampel. ${result.note}`;}catch(e){$c('creatorStatus').textContent=e.message;}finally{b.disabled=false;}};
    $c('applyCrop').onclick=async()=>{try{if(part){base.framing={...base.framing,[part]:framing};base.crop='split';base.canvas='portrait';}else{base.framing=framing;base.crop='manual';}await editor.save(true);editor.renderInspector();editor.schedulePreview();close();}catch(e){$c('creatorStatus').textContent=e.message;}};paint();
  }
  async function upload(file,target='#source') {
    if(!file)return;
    toast(`Mengimpor ${file.name}…`);
    const response=await fetch('/api/source-upload',{method:'POST',headers:{'x-filename':encodeURIComponent(file.name)},body:file});
    const result=await response.json();if(!response.ok)throw new Error(result.detail||'Upload gagal');
    document.querySelector(target).value=result.path;onSourceChanged();toast('Video siap diproses.');
  }
  document.addEventListener('DOMContentLoaded',()=>{const source=document.querySelector('#source');const area=source?.closest('.card');if(!area)return;
    area.addEventListener('dragover',e=>{if(e.dataTransfer.types.includes('Files')){e.preventDefault();area.classList.add('drop-active');}});
    area.addEventListener('dragleave',()=>area.classList.remove('drop-active'));
    area.addEventListener('drop',e=>{if(e.dataTransfer.files.length){e.preventDefault();area.classList.remove('drop-active');upload(e.dataTransfer.files[0]).catch(err=>toast(err.message,'error'));}});
  });
  return {words,crop,upload,shiftFraming};
})();
