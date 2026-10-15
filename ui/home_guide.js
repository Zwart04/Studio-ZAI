const HomeGuide = (() => {
  const providers = {
    openai: {name:'OpenAI', badge:'API berbayar', key:'https://platform.openai.com/api-keys', docs:'https://developers.openai.com/api/docs/quickstart', pricing:'https://developers.openai.com/api/docs/pricing', steps:'Masuk ke OpenAI Platform → buat API key pada proyek → siapkan saldo API. Langganan ChatGPT tidak otomatis menjadi saldo API.'},
    anthropic: {name:'Anthropic', badge:'API berbayar', key:'https://platform.claude.com/settings/keys', docs:'https://platform.claude.com/docs/en/api/overview', pricing:'https://platform.claude.com/docs/en/about-claude/pricing', steps:'Masuk ke Claude Console → API keys → buat key. Periksa kredit dan batas pemakaian akun sebelum menggunakan API.'},
    gemini: {name:'Google Gemini', badge:'Ada kuota gratis', key:'https://aistudio.google.com/apikey', docs:'https://ai.google.dev/gemini-api/docs/api-key', pricing:'https://ai.google.dev/gemini-api/docs/pricing', steps:'Masuk ke Google AI Studio → Get API key → pilih atau buat proyek → salin key. Gratis hanya untuk model dan wilayah yang memenuhi syarat; kuota mengikuti akun. Data pada layanan gratis dapat digunakan untuk peningkatan produk sesuai kebijakan Google.'},
    groq: {name:'Groq', badge:'Ada paket gratis', key:'https://console.groq.com/keys', docs:'https://console.groq.com/docs/quickstart', pricing:'https://console.groq.com/docs/rate-limits', steps:'Masuk ke Groq Console → API Keys → Create API Key. Paket Free memiliki batas permintaan dan token per model; lihat halaman Limits akun.'},
    deepseek: {name:'DeepSeek', badge:'API berbayar', key:'https://platform.deepseek.com/api_keys', docs:'https://api-docs.deepseek.com/', pricing:'https://api-docs.deepseek.com/quick_start/pricing/', steps:'Masuk ke DeepSeek Platform → API keys → buat key → periksa saldo API. Biaya mengikuti model, token, cache, dan jam pemakaian.'},
    compatible: {name:'API kompatibel / Ollama', badge:'Sesuai layanan', steps:'Atur alamat endpoint di Pengaturan. Untuk server lokal, API key mengikuti konfigurasi server. Biaya dan model mengikuti penyedia endpoint tersebut.'},
  };
  let discovered = null;
  function showProvider() {
    discovered = null;
    const id=document.querySelector('#aiProvider').value, p=providers[id], host=document.querySelector('#providerHelp');
    host.replaceChildren();
    if(p){
      const identity=document.createElement('div');identity.className='provider-identity';
      if(id!=='compatible'){const img=document.createElement('img');img.id='providerLogo';img.src=`/assets/providers/${id}.png`;img.alt=`Logo ${p.name}`;img.width=32;img.height=32;identity.append(img);}
      const name=document.createElement('strong');name.textContent=p.name;identity.append(name);host.append(identity);
      const badge=document.createElement('strong');badge.className='provider-access';badge.textContent=p.badge;
      const copy=document.createElement('p');copy.textContent=p.steps;host.append(badge,copy);
      const links=document.createElement('div');links.className='provider-links';
      for(const [field,label] of [['key','Dapatkan API key ↗'],['docs','Panduan resmi ↗'],['pricing','Harga & batas ↗']]){
        if(!p[field])continue;
        const a=document.createElement('a');a.href=p[field];a.target='_blank';a.rel='noopener noreferrer';a.textContent=label;links.append(a);
      }
      host.append(links);
    }
    document.querySelector('#aiModelDetail').textContent='Deteksi model di akun Anda untuk memilih berdasarkan prioritas.';
    document.querySelector('#aiPriorityNote').textContent='Termurah membandingkan model dengan harga tercatat. Paling pintar adalah saran keluarga model, bukan jaminan kualitas. Deteksi model untuk provider ini terlebih dahulu.';
    updateButtons();
  }
  function updateButtons(){
    const select=document.querySelector('#aiModelPriority');select.disabled=!discovered;select.value='manual';
    for(const option of select.options)if(option.value!=='manual')option.disabled=!discovered?.guidance?.[option.value];
  }
  function describe(){
    const id=document.querySelector('#aiModel').value, row=discovered?.models.find(m=>m.id===id);
    const price=row?.price;
    document.querySelector('#aiModelDetail').textContent=price
      ? `${id} · USD ${price.input} input / ${price.output} output per 1 juta token. Tarif standar konteks pendek; belum termasuk diskon atau kuota gratis. Diperiksa ${price.checked}.`
      : 'Harga model ini belum tercatat. Periksa harga resmi dan batas akun sebelum menjalankan analisis.';
  }
  function models(result){
    discovered=result;
    if(!discovered.guidance)discovered.guidance={recommended:result.recommended};
    const select=document.querySelector('#aiModel'), selected=select.value;
    select.replaceChildren(new Option('Otomatis · saran provider','auto'));
    const suggested=document.createElement('optgroup');suggested.label='Pilihan utama';
    const others=document.createElement('optgroup');others.label='Model lain di akun';
    for(const row of result.models){
      const tags=Object.entries({recommended:'Rekomendasi',cheapest:'Termurah',smartest:'Paling pintar'}).filter(([key])=>result.guidance[key]===row.id).map(([,label])=>label);
      const option=new Option(`${row.label||row.id}${tags.length?' · '+tags.join(' / '):''}`,row.id);
      (tags.length?suggested:others).append(option);
    }
    if(suggested.children.length)select.append(suggested);if(others.children.length)select.append(others);select.value=selected;
    updateButtons();document.querySelector('#aiModelPriority').value=selected===result.recommended?'recommended':'manual';describe();
    document.querySelector('#aiPriorityNote').textContent=result.guidance.note || 'Daftar mengikuti model yang tersedia di akun. Harga dan kemampuan belum tersedia.';
  }
  function init(){
    const layout=document.querySelector('.source-settings'), analysis=document.querySelector('[aria-labelledby=analysisHeading]');
    layout.classList.add('home-feature-grid');
    // Dua wadah kolom eksplisit: tiap kolom mengalir sendiri sehingga bagian
    // dengan tinggi berbeda tidak pernah meninggalkan lubang kosong di tengah
    // kolom (multikolom CSS merusak grid kanvas di Chromium).
    // Kiri = model & transkrip. Kanan = bentuk hasil & subtitle.
    const colLeft=document.createElement('div'), colRight=document.createElement('div');
    colLeft.className=colRight.className='home-col';
    colLeft.append(analysis);
    colRight.append(document.getElementById('clipResultSettings'));
    layout.append(colLeft,colRight);
    const transcript=document.createElement('section');transcript.className='source-setting-section';transcript.id='transcriptSettings';
    transcript.innerHTML='<div class="setting-heading"><h3>Transkrip &amp; audio</h3></div>';
    const asr=document.querySelector('#asrSpeed').closest('.field'), checkbox=document.querySelector('#useTranscript'), explanation=checkbox.nextElementSibling;
    transcript.append(asr,checkbox,explanation,document.querySelector('#lang').closest('.grid-2'),document.querySelector('#audioTrackWrap'));
    colLeft.append(transcript);
    const old=document.querySelector('#advDetails'), advanced=old.querySelector('.advanced-content');
    const extras=document.createElement('div');extras.id='momentExtras';extras.className='moment-extras';
    extras.append(document.querySelector('#analysisMode').closest('label'),document.querySelector('#reviewFirst').closest('label'),advanced.querySelector('p'),document.querySelector('#useLlm'));
    analysis.append(extras);
    const subtitles=document.createElement('section');subtitles.id='advDetails';subtitles.className='source-setting-section home-subtitle-settings';
    subtitles.innerHTML='<div class="setting-heading"><h3>Subtitle &amp; animasi</h3></div>';
    subtitles.append(document.querySelector('#subPos').closest('.field'),document.querySelector('.home-caption-style'));
    old.replaceWith(subtitles);colRight.append(subtitles);
    const gguf=document.querySelector('.model-advanced');
    if(gguf?.tagName==='DETAILS'){const group=document.createElement('div');group.className='model-advanced';gguf.querySelector('summary').remove();group.append(...gguf.childNodes);gguf.replaceWith(group);}
    const panel=document.querySelector('#aiPanel');panel.classList.add('online-model-form');
    const help=document.createElement('div');help.id='providerHelp';help.className='provider-help';panel.querySelector('.grid-2').after(help);
    const priority=document.createElement('div');priority.className='model-priorities';
    priority.innerHTML='<label for="aiModelPriority">Pilih berdasarkan</label><select id="aiModelPriority" disabled><option value="manual">Pilih model sendiri</option><option value="recommended">Rekomendasi</option><option value="cheapest">Termurah dari harga tercatat</option><option value="smartest">Paling pintar · saran keluarga model</option></select><p id="aiPriorityNote" class="field-help">Pilih provider, masukkan API key, lalu deteksi model.</p><p id="aiModelDetail" role="status" class="model-price-detail"></p>';
    panel.append(priority);
    priority.querySelector('select').onchange=event=>{
      const id=discovered?.guidance?.[event.target.value];if(!id)return;
      const select=document.querySelector('#aiModel');if(![...select.options].some(o=>o.value===id))return;
      select.value=id;describe();
    };
    document.querySelector('#aiProvider').addEventListener('change',showProvider);
    document.querySelector('#aiModel').addEventListener('change',()=>{updateButtons();describe();});
    document.querySelector('#aiKey').addEventListener('input',()=>{discovered=null;document.querySelector('#aiModel').replaceChildren(new Option('Otomatis · saran provider','auto'));updateButtons();document.querySelector('#aiModelDetail').textContent='API key berubah. Deteksi ulang model untuk akun ini.';});
    const performance=document.createElement('details');performance.className='performance-controls home-fold';
    performance.innerHTML='<summary>Kinerja laptop</summary><label for="performanceMode">Pemakaian CPU & RAM</label><select id="performanceMode"><option value="balanced">Seimbang</option><option value="light">Hemat RAM · laptop lama</option></select><p class="field-help">Hemat RAM memilih Whisper tiny dan analisis tanpa LLM. Preview 360p disiapkan satu per satu; ekspor tetap memakai sumber asli.</p><div class="gguf-actions"><button type="button" class="ghost" id="pickSmallGguf">Pilih GGUF terkecil</button><button type="button" class="ghost" id="pickNoLlm">Tanpa LLM · paling ringan</button></div><p class="field-help">GGUF hingga 1.200 MB diberi label Ringan. Ukuran berkas bukan total kebutuhan RAM. Model harus sudah tersedia di komputer.</p>';
    document.querySelector('#localLlmFields').append(performance);
    const performanceMode=performance.querySelector('#performanceMode');
    api('/api/settings').then(settings=>{performanceMode.value=settings.performance_mode||'balanced';}).catch(()=>{});
    performanceMode.onchange=async()=>{
      try {await api('/api/settings',{method:'POST',body:JSON.stringify({values:{performance_mode:performanceMode.value}})});
        if(performanceMode.value==='light'){$('#asrSpeed').value='fast';$('#localModel').value='';$('#localModel').dispatchEvent(new Event('change'));}
      }catch(error){toast(error.message,'error');}
    };
    performance.querySelector('#pickNoLlm').onclick=()=>{$('#localModel').value='';$('#localModel').dispatchEvent(new Event('change'));};
    performance.querySelector('#pickSmallGguf').onclick=()=>{const select=$('#ggufModel');if(select.options.length>1){select.selectedIndex=1;$('#localModelStatus').textContent='GGUF terkecil dipilih. Tekan Muat model untuk menjalankannya.';}else $('#localModelStatus').textContent='Belum ada GGUF lokal. Gunakan Tanpa LLM untuk mode paling ringan.';};
    showProvider();
  }
  return {init,models};
})();
