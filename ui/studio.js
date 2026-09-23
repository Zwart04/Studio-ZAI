/* Optional studio tools. Uses the same design tokens and background jobs. */
(() => {
  const icons = {image:'<rect x="3" y="3" width="18" height="18" rx="3"/><circle cx="8" cy="8" r="1"/><path d="m3 17 6-6 4 4 3-3 5 5"/>'};
  const icon = name => `<svg class="ico" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">${icons[name]}</svg>`;
  const nav = document.createElement('button');nav.dataset.page='images';nav.innerHTML=icon('image')+'<span>Gambar</span>';nav.onclick=()=>setPage('images');
  $('#nav').insertBefore(nav,$('#nav [data-page="models"]'));
  const shortcuts=document.createElement('div');shortcuts.className='studio-shortcuts';
  shortcuts.innerHTML='<button data-tool="video"><strong>Video</strong><span>Potong, susun, beri subtitle</span></button><button data-tool="voice"><strong>Suara</strong><span>Narasi dan rekamanmu</span></button><button data-tool="images"><strong>Gambar</strong><span>Dari ide menjadi visual</span></button>';
  $('#page-home .lead').after(shortcuts);
  shortcuts.querySelectorAll('button').forEach(button=>button.onclick=()=>button.dataset.tool==='video' ? $('#source').focus() : setPage(button.dataset.tool));
  const page=document.createElement('section');page.className='page';page.id='page-images';
  page.innerHTML=`<h1>Studio gambar</h1><p class="lead">Jelaskan idemu. Pilih mesin lokal atau layanan online di Pengaturan.</p>
    <div class="card"><label for="imagePrompt">Gambar seperti apa yang ingin dibuat?</label><textarea id="imagePrompt" rows="4" placeholder="Contoh: meja kerja minimalis dengan cahaya pagi, fotografi produk"></textarea>
    <p class="field-help">Online mengirim deskripsi ke penyedia dan dapat memakai kuota API. Lokal memakai server Stable Diffusion milikmu; mulai dari 512 × 512 agar ringan.</p>
    <div class="row"><button class="primary" id="imageGenerate">Buat gambar</button><button id="imageSettings">Atur penyedia</button></div></div>
    <h2>Hasil gambar</h2><div id="imageGallery" class="image-gallery"></div>`;
  $('main').append(page);
  $('#imageSettings').onclick=()=>setPage('settings');
  $('#imageGenerate').onclick=async()=>{try{const prompt=$('#imagePrompt').value.trim();if(!prompt)return toast('Isi deskripsi gambar.');const job=await api('/api/images',{method:'POST',body:JSON.stringify({prompt})});trackJob(job);}catch(e){toast(e.message,'error');}};
  window.renderImages=async()=>{
    const images=await api('/api/images');
    $('#imageGallery').innerHTML=images.length ? images.map(p=>`<article class="card"><img src="${mediaUrl(p.path)}" alt="Hasil gambar" loading="lazy"><div class="row"><a class="mini" download href="${mediaUrl(p.path)}">Simpan gambar</a><button data-delete-image="${p.name}">Hapus</button></div></article>`).join('') : '<div class="empty">Hasil gambar akan tersimpan di sini.</div>';
    $('#imageGallery').querySelectorAll('[data-delete-image]').forEach(b=>b.onclick=async()=>{await api('/api/images/'+b.dataset.deleteImage,{method:'DELETE'});await renderImages();});
  };

  const settings=document.createElement('div');settings.id='aiSettings';
  $('#page-settings > h1').after(settings);
  window.renderAiSettings=async()=>{
    const [{providers},saved]=await Promise.all([api('/api/ai/providers'),api('/api/settings')]);
    settings.innerHTML='<h2>AI opsional</h2><p class="field-help">Editor dan model suara lokal tetap bisa dipakai tanpa akun. Isi API key layananmu untuk fitur online. Langganan ChatGPT bukan API key. Di Windows, kunci disimpan dengan proteksi akun Windows.</p>'+[
      ['ai','Teks & pemilihan momen','text','Contoh: model teks yang tersedia di akunmu'],
      ['image','Pembuatan gambar','image','gpt-image-1-mini / sd-cpp-local'],
      ['speech','Suara online','speech','gpt-4o-mini-tts']
    ].map(([kind,label,capability,hint])=>`<details class="card ai-profile"><summary>${label}</summary><div class="grid-2"><label>Penyedia<select data-ai="${kind}_provider"><option value="">Belum diatur</option>${Object.entries(providers).filter(([,p])=>p[capability]).map(([id,p])=>`<option value="${id}">${p.label}</option>`).join('')}</select></label><label>Model<input data-ai="${kind}_model" placeholder="${hint}"></label><label>Alamat API<input data-ai="${kind}_base_url" placeholder="Diisi sesuai penyedia"></label><label>API key<input data-ai="${kind}_api_key" type="password" autocomplete="off" placeholder="${saved[kind+'_api_key'] ? 'Tersimpan · kosongkan untuk mempertahankan' : 'API key milikmu'}"></label></div><button class="mini" data-clear-key="${kind}">Hapus kunci tersimpan</button></details>`).join('')+'<button id="saveAiSettings" class="primary">Simpan pengaturan AI</button>';
    settings.querySelectorAll('[data-ai]').forEach(input=>{
      if(!input.dataset.ai.endsWith('_api_key'))input.value=saved[input.dataset.ai] || '';
      if(input.tagName==='SELECT')input.onchange=()=>{const kind=input.dataset.ai.replace('_provider','');settings.querySelector(`[data-ai="${kind}_base_url"]`).value=providers[input.value]?.url || '';};
    });
    settings.querySelectorAll('[data-clear-key]').forEach(b=>b.onclick=()=>{const field=settings.querySelector(`[data-ai="${b.dataset.clearKey}_api_key"]`);field.value='';field.dataset.clear='yes';field.placeholder='Akan dihapus saat disimpan';});
    $('#saveAiSettings').onclick=async()=>{
      const values={};settings.querySelectorAll('[data-ai]').forEach(input=>{const key=input.dataset.ai;values[key]=key.endsWith('_api_key')&&!input.value&&input.dataset.clear!=='yes' ? saved[key] || '' : input.value;});
      try{state.settings=await api('/api/settings',{method:'POST',body:JSON.stringify({values})});await renderAiSettings();toast('Pengaturan AI tersimpan.');}catch(e){toast(e.message,'error');}
    };
  };

  const voiceControls=document.createElement('div');voiceControls.className='grid-2';
  voiceControls.innerHTML='<label>Mesin suara<select id="ttsEngine"><option value="local">Lokal · Piper</option><option value="cloud">Online · OpenAI</option></select></label><label id="cloudVoiceWrap" hidden>Karakter suara<select id="cloudVoice">'+['marin','cedar','alloy','ash','ballad','coral','echo','fable','nova','onyx','sage','shimmer','verse'].map(v=>`<option>${v}</option>`).join('')+'</select></label>';
  $('#ttsText').before(voiceControls);
  $('#ttsEngine').onchange=()=>{const online=$('#ttsEngine').value==='cloud';$('#cloudVoiceWrap').hidden=!online;renderVoice();$('#ttsVoice').disabled=online || !$('#ttsVoice').value;};
  $('#ttsLang').addEventListener('change',renderVoice);
  const reference=document.createElement('label');reference.textContent='Teks persis dari rekaman contoh';
  const referenceInput=document.createElement('textarea');referenceInput.id='referenceText';referenceInput.rows=2;referenceInput.placeholder='Tuliskan ucapan pada rekaman contoh';reference.append(referenceInput);$('#cloneSample').closest('.field')?.after(reference);
  if(!$('#referenceText'))$('#pickSample').parentElement.after(reference);
  $('#cloneLang').innerHTML='<option value="en">English · ZipVoice</option><option value="zh">Mandarin · ZipVoice</option>';
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
        try{const response=await fetch('/api/voice-sample',{method:'POST',headers:{'Content-Type':recorder.mimeType},body:new Blob(parts,{type:recorder.mimeType})});const data=await response.json();if(!response.ok)throw Error(data.detail);$('#cloneSample').value=data.path;toast('Rekaman siap dipakai sebagai contoh suara.');}
        catch(e){toast(e.message,'error');}finally{mic.disabled=false;mic.textContent='● Rekam mikrofon';}
      };
      recorder.start();mic.textContent='■ Selesai merekam (maks. 30 dtk)';timer=setTimeout(()=>{if(recorder.state==='recording')recorder.stop();},30000);
    }catch(e){stream?.getTracks().forEach(t=>t.stop());toast('Mikrofon tidak tersedia atau izin belum diberikan. Pilih rekaman dari berkas.','error');}
  };
  window.addEventListener('pagehide',()=>{stream?.getTracks().forEach(t=>t.stop());clearTimeout(timer);});
  window.stopStudioRecording=()=>{if(recorder?.state==='recording')recorder.stop();};
})();
