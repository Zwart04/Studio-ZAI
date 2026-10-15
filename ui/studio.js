/* Optional studio tools. Uses the same design tokens and background jobs. */
(() => {
  const icons = {image:'<rect x="3" y="3" width="18" height="18" rx="3"/><circle cx="8" cy="8" r="1"/><path d="m3 17 6-6 4 4 3-3 5 5"/>'};
  const icon = name => `<svg class="ico" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">${icons[name]}</svg>`;
  const nav = document.createElement('button');nav.dataset.page='images';nav.innerHTML=icon('image')+'<span>Gambar</span>';nav.onclick=()=>setPage('images');
  $('#nav').insertBefore(nav,$('#nav [data-page="models"]'));
  const shortcuts=document.createElement('div');shortcuts.className='studio-shortcuts';
  shortcuts.innerHTML='<button data-tool="video"><strong>Video</strong><span>Potong, susun, beri subtitle</span></button><button data-tool="voice"><strong>Suara</strong><span>Narasi dan rekamanmu</span></button><button data-tool="images"><strong>Gambar</strong><span>Dari ide menjadi visual</span></button>';
  $('#page-home #processingCard').after(shortcuts);
  shortcuts.querySelectorAll('button').forEach(button=>button.onclick=()=>button.dataset.tool==='video' ? $('#source').focus() : setPage(button.dataset.tool));
  const page=document.createElement('section');page.className='page';page.id='page-images';
  page.innerHTML=`<h1>Studio gambar</h1><p class="lead">Buat visual dari deskripsi. Model lokal bekerja di komputer tanpa mengirim teks ke internet.</p>
    <div class="source-modes image-modes" role="group" aria-label="Mesin gambar"><button type="button" class="active" data-image-mode="local">Lokal · offline</button><button type="button" data-image-mode="cloud">Online · opsional</button></div>
    <div class="card image-model-card" id="imageModelCard" aria-live="polite"></div>
    <div class="card image-prompt-card"><label for="imagePrompt">Gambar seperti apa yang ingin dibuat?</label><textarea id="imagePrompt" rows="4" maxlength="2000" placeholder="Contoh: meja kerja minimalis dengan cahaya pagi, fotografi produk"></textarea>
    <div class="row image-actions"><button class="primary" id="imageGenerate">Buat gambar</button><button class="ghost" id="imageSettings">Atur penyedia online</button></div></div>
    <h2>Hasil tersimpan</h2><div id="imageGallery" class="image-gallery"></div>`;
  $('main').append(page);
  let imageMode='local', imageModel=null;
  function updateImageMode(){
    page.querySelectorAll('[data-image-mode]').forEach(button=>button.classList.toggle('active',button.dataset.imageMode===imageMode));
    $('#imageGenerate').disabled=imageMode==='local'&&!imageModel?.installed;
    $('#imageSettings').hidden=imageMode==='local';
    $('#imageModelCard').innerHTML=imageMode==='local'
      ? `<div class="spread"><div><h3>SDXS-512 <span class="muted">· 512 × 512</span></h3><p class="field-help">${imageModel?.installed ? 'Model lokal siap. Deskripsi dan hasil tetap di perangkatmu.' : 'Unduh sekali sekitar 683 MB. Setelah terpasang, gambar dapat dibuat offline tanpa server.'}</p></div>${imageModel?.installed ? '<span class="badge ok">Siap</span>' : '<button class="primary" id="imageModelDownload"'+(imageModel?'':' disabled')+'>Unduh model lokal · 683 MB</button>'}</div>`
      : `<div class="spread"><div><h3>Layanan online</h3><p class="field-help">Deskripsi dikirim ke penyedia pilihanmu. Siapkan API key di Pengaturan.</p></div><button class="ghost" id="imageCloudSettings">Atur API key</button></div>`;
    $('#imageModelDownload')?.addEventListener('click',async()=>{
      try{
        const button=$('#imageModelDownload');button.disabled=true;button.textContent='Mengunduh…';
        const job=await api('/api/models/sdxs-512/download',{method:'POST'});
        trackJob(job);
        const events=new EventSource(`/api/jobs/${job.id}/events`);
        events.onmessage=async event=>{const data=JSON.parse(event.data);if(data.type==='end'){events.close();await refreshImageModel();}};
        events.onerror=()=>events.close();
      }catch(error){toast(error.message,'error');await refreshImageModel();}
    });
    $('#imageCloudSettings')?.addEventListener('click',()=>setPage('settings'));
  }
  async function refreshImageModel(){
    try{const data=await api('/api/models');imageModel=(data.models||[]).find(model=>model.id==='sdxs-512')||null;updateImageMode();}
    catch(error){$('#imageModelCard').textContent='Status model belum tersedia: '+error.message;}
  }
  page.querySelectorAll('[data-image-mode]').forEach(button=>button.onclick=()=>{imageMode=button.dataset.imageMode;updateImageMode();});
  $('#imageSettings').onclick=()=>setPage('settings');
  $('#imageGenerate').onclick=async()=>{
    try{
      const prompt=$('#imagePrompt').value.trim();if(!prompt)return toast('Isi deskripsi gambar.');
      const job=await api('/api/images',{method:'POST',body:JSON.stringify({prompt,provider:imageMode==='local'?'sdxs_local':'cloud'})});
      trackJob(job);
    }catch(error){toast(error.message,'error');}
  };
  window.renderImages=async()=>{
    const [images]=await Promise.all([api('/api/images'),refreshImageModel()]);
    $('#imageGallery').innerHTML=images.length ? images.map(p=>`<article class="card"><img src="${mediaUrl(p.path)}" alt="Hasil gambar" loading="lazy"><div class="row"><a class="mini" download href="${mediaUrl(p.path)}">Simpan gambar</a><button class="mini danger" data-delete-image="${escapeHtml(p.name)}">Hapus</button></div></article>`).join('') : '<div class="empty">Belum ada gambar. Hasilmu akan tampil di sini.</div>';
    $('#imageGallery').querySelectorAll('[data-delete-image]').forEach(b=>b.onclick=async()=>{await api('/api/images/'+encodeURIComponent(b.dataset.deleteImage),{method:'DELETE'});await renderImages();});
  };

  const settings=document.createElement('div');settings.id='aiSettings';
  $('#page-settings > h1').after(settings);
  window.renderAiSettings = async () => {
    const [{providers}, saved] = await Promise.all([api('/api/ai/providers'), api('/api/settings')]);
    settings.innerHTML = '<h2>AI online · timestamp & momen</h2><p class="field-help">Pilih provider, masukkan API key, lalu model yang tersedia dideteksi dan disarankan. Deteksi hanya meminta daftar model. Saat analisis online diaktifkan, transkrip dikirim ke provider pilihanmu. API key tetap disimpan dengan proteksi akun Windows.</p>' + [
      ['ai','Timestamp & pemilihan momen','text'], ['image','Gambar','image'], ['speech','Suara online','speech']
    ].map(([kind,label,capability]) => `<details class="card ai-profile" data-kind="${kind}" ${kind==='ai'?'open':''}><summary>${label}</summary>
      <div class="grid-2"><label>Provider<select data-ai="${kind}_provider"><option value="">Pilih provider</option>${Object.entries(providers).filter(([,p])=>p[capability]).map(([id,p])=>`<option value="${id}">${escapeHtml(p.label)}</option>`).join('')}</select></label>
      <label>API key<input data-ai="${kind}_api_key" type="password" autocomplete="off" spellcheck="false" placeholder="${saved[kind+'_api_key']?'Tersimpan · kosongkan untuk mempertahankan':'API key milikmu'}"></label></div>
      <div class="row"><button data-detect="${kind}" class="ghost">Deteksi & sarankan model</button><button class="mini danger" data-clear-key="${kind}">Hapus kunci</button></div>
      <label>Model<select data-model="${kind}"><option value="auto">Otomatis · saran provider</option><option value="custom">Isi model manual</option></select></label>
      <input data-ai="${kind}_model" hidden placeholder="ID model dari provider">
      <label data-url-wrap="${kind}" hidden>Alamat API<input data-ai="${kind}_base_url" placeholder="Alamat server kompatibel"></label>
      <p data-model-status="${kind}" class="field-help" role="status"></p></details>`).join('') + '<button id="saveAiSettings" class="primary">Simpan pengaturan AI</button>';
    settings.querySelectorAll('.ai-profile').forEach(card => {
      const kind=card.dataset.kind, field=name=>card.querySelector(`[data-ai="${kind}_${name}"]`), select=card.querySelector('[data-model]'), status=card.querySelector('[data-model-status]'), button=card.querySelector('[data-detect]');
      let revision=0;
      field('provider').value=saved[kind+'_provider']||'';
      field('base_url').value=saved[kind+'_base_url']||providers[field('provider').value]?.url||'';
      field('model').value=saved[kind+'_model']||'auto';
      if(field('model').value!=='auto') { select.add(new Option(field('model').value+' · tersimpan',field('model').value),1);select.value=field('model').value;field('model').hidden=true; }
      function refreshUrl() {card.querySelector('[data-url-wrap]').hidden=!['compatible','sd_local'].includes(field('provider').value);button.hidden=field('provider').value==='sdxs_local';}
      refreshUrl();
      field('provider').onchange=()=>{revision++;field('base_url').value=providers[field('provider').value]?.url||'';field('api_key').value='';field('api_key').dataset.clear='yes';field('api_key').placeholder='Masukkan API key provider ini';field('model').value='auto';field('model').hidden=true;select.innerHTML='<option value="auto">Otomatis · saran provider</option><option value="custom">Isi model manual</option>';status.textContent='';refreshUrl();};
      field('api_key').oninput=()=>revision++;
      field('base_url').oninput=()=>revision++;
      select.onchange=()=>{field('model').hidden=select.value!=='custom';if(select.value!=='custom')field('model').value=select.value;};
      async function detect() {
        const current=++revision;button.disabled=true;status.textContent='Memuat model dari provider…';
        try {
          const result=await api('/api/ai/models',{method:'POST',body:JSON.stringify({kind,provider:field('provider').value,base_url:field('base_url').value,api_key:field('api_key').value,use_saved_key:!field('api_key').value&&field('api_key').dataset.clear!=='yes'})});
          if(current!==revision||!card.isConnected)return;
          select.innerHTML='<option value="auto">Otomatis · saran provider</option>'+result.models.map(m=>`<option value="${escapeHtml(m.id)}">${escapeHtml(m.label)}${m.id===result.recommended?' · disarankan':''}</option>`).join('')+'<option value="custom">Isi model manual</option>';
          select.value=result.recommended;field('model').value=result.recommended;field('model').hidden=true;status.textContent=`${result.models.length} model terdeteksi. ${result.note}`;
        } catch(error) {if(current===revision)status.textContent=error.message;} finally {if(card.isConnected)button.disabled=false;}
      }
      button.onclick=detect;
      field('api_key').onblur=()=>{if(field('api_key').value.trim()&&field('provider').value)detect();};
      card.querySelector('[data-clear-key]').onclick=()=>{revision++;field('api_key').value='';field('api_key').dataset.clear='yes';field('api_key').placeholder='Akan dihapus saat disimpan';status.textContent='';};
    });
    $('#saveAiSettings').onclick=async()=>{
      const values={};settings.querySelectorAll('[data-ai]').forEach(input=>{const key=input.dataset.ai;values[key]=key.endsWith('_api_key')&&!input.value&&input.dataset.clear!=='yes'?saved[key]||'':input.value.trim();});
      try {state.settings=await api('/api/settings',{method:'POST',body:JSON.stringify({values})});await renderAiSettings();toast('Pengaturan AI tersimpan.');} catch(error){toast(error.message,'error');}
    };
  };

  const voiceControls=document.createElement('div');voiceControls.className='grid-2';
  voiceControls.innerHTML='<label>Mesin suara<select id="ttsEngine"><option value="local">Lokal · offline</option><option value="cloud">Online · OpenAI</option></select></label><label id="cloudVoiceWrap" hidden>Karakter suara<select id="cloudVoice">'+['marin','cedar','alloy','ash','ballad','coral','echo','fable','nova','onyx','sage','shimmer','verse'].map(v=>`<option>${v}</option>`).join('')+'</select></label>';
  $('#ttsText').before(voiceControls);
  $('#ttsEngine').onchange=()=>{const online=$('#ttsEngine').value==='cloud';$('#cloudVoiceWrap').hidden=!online;$('#ttsLocalVoiceWrap').hidden=online;renderVoice();$('#ttsVoice').disabled=online || !$('#ttsVoice').value;};
  $('#ttsLang').addEventListener('change',renderVoice);
  const mic=document.createElement('button');mic.id='recordSample';mic.textContent='● Rekam mikrofon';mic.className='ghost';$('#pickSample').after(mic);
  let recorder=null,stream=null,timer=null;
  mic.onclick=async()=>{
    if(recorder?.state==='recording'){recorder.stop();return;}
    try{
      stream=await navigator.mediaDevices.getUserMedia({audio:true});
      const parts=[];recorder=new MediaRecorder(stream);
      recorder.ondataavailable=e=>{if(e.data.size)parts.push(e.data);};
      recorder.onstop=async()=>{
        clearTimeout(timer);stream.getTracks().forEach(t=>t.stop());mic.disabled=true;mic.textContent='Menyimpan rekaman…';
        try{const response=await fetch('/api/voice-sample',{method:'POST',headers:{'Content-Type':recorder.mimeType},body:new Blob(parts,{type:recorder.mimeType})});const data=await response.json();if(!response.ok)throw Error(data.detail);$('#cloneSample').value=data.path;$('#cloneSampleName').textContent='Rekaman mikrofon · siap';const player=$('#cloneSamplePlayer');player.src=mediaUrl(data.path);player.hidden=false;toast('Rekaman siap dipakai sebagai contoh suara.');}
        catch(e){toast(e.message,'error');}finally{mic.disabled=false;mic.textContent='● Rekam mikrofon';}
      };
      recorder.start();mic.textContent='■ Selesai merekam (maks. 30 dtk)';timer=setTimeout(()=>{if(recorder.state==='recording')recorder.stop();},30000);
    }catch(e){stream?.getTracks().forEach(t=>t.stop());toast('Mikrofon tidak tersedia atau izin belum diberikan. Pilih rekaman dari berkas.','error');}
  };
  window.addEventListener('pagehide',()=>{stream?.getTracks().forEach(t=>t.stop());clearTimeout(timer);});
  window.stopStudioRecording=()=>{if(recorder?.state==='recording')recorder.stop();};
})();
