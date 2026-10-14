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
    document.querySelectorAll('[data-provider-pick]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.providerPick===id)));
    host.replaceChildren();
    if(p){
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
    document.querySelectorAll('[data-model-priority]').forEach(button=>{
      button.disabled=!discovered?.guidance?.[button.dataset.modelPriority];
      button.title=button.disabled ? (discovered ? 'Belum ada data yang cukup untuk model pada akun ini.' : 'Deteksi model terlebih dahulu.') : '';
      button.setAttribute('aria-pressed','false');
    });
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
    updateButtons();describe();
    document.querySelector('#aiPriorityNote').textContent=result.guidance.note || 'Daftar mengikuti model yang tersedia di akun. Harga dan kemampuan belum tersedia.';
  }
  function init(){
    const layout=document.querySelector('.source-settings'), analysis=document.querySelector('[aria-labelledby=analysisHeading]');
    layout.classList.add('home-feature-grid');
    const transcript=document.createElement('section');transcript.className='source-setting-section';transcript.id='transcriptSettings';
    transcript.innerHTML='<div class="setting-heading"><h3>Transkrip & audio</h3><p>Ubah ucapan menjadi teks dan pilih bahasa sumber.</p></div>';
    const asr=document.querySelector('#asrSpeed').closest('.field'), checkbox=document.querySelector('#useTranscript'), explanation=checkbox.nextElementSibling;
    transcript.append(asr,checkbox,explanation,document.querySelector('#lang').closest('.grid-2'),document.querySelector('#audioTrackWrap'));
    layout.append(transcript);
    const old=document.querySelector('#advDetails'), advanced=old.querySelector('.advanced-content');
    const extras=document.createElement('div');extras.id='momentExtras';extras.className='moment-extras';
    extras.append(document.querySelector('#analysisMode').closest('label'),document.querySelector('#reviewFirst').closest('label'),advanced.querySelector('p'),document.querySelector('#useLlm'));
    analysis.append(extras);
    const subtitles=document.createElement('section');subtitles.id='advDetails';subtitles.className='source-setting-section home-subtitle-settings';
    subtitles.innerHTML='<div class="setting-heading"><h3>Subtitle & animasi</h3><p>Atur posisi teks, sorotan kata, dan gerakan saat berbicara.</p></div>';
    subtitles.append(document.querySelector('#subPos').closest('.field'),document.querySelector('.home-caption-style'));
    old.replaceWith(subtitles);layout.append(subtitles);
    const gguf=document.querySelector('.model-advanced');
    if(gguf?.tagName==='DETAILS'){const group=document.createElement('div');group.className='model-advanced';gguf.querySelector('summary').remove();group.append(...gguf.childNodes);gguf.replaceWith(group);}
    const picker=document.createElement('div');picker.className='provider-picker';picker.setAttribute('aria-label','Pilih provider online');
    for(const [id,p] of Object.entries(providers)){
      const button=document.createElement('button');button.type='button';button.dataset.providerPick=id;button.setAttribute('aria-pressed','false');
      if(id!=='compatible'){const img=document.createElement('img');img.src=`/assets/providers/${id}.png`;img.alt='';img.width=28;img.height=28;button.append(img);}
      const name=document.createElement('strong');name.textContent=p.name;const badge=document.createElement('small');badge.textContent=p.badge;button.append(name,badge);
      button.onclick=()=>{const select=document.querySelector('#aiProvider');if(select.value!==id){select.value=id;select.dispatchEvent(new Event('change'));}};picker.append(button);
    }
    const panel=document.querySelector('#aiPanel');panel.prepend(picker);
    const help=document.createElement('div');help.id='providerHelp';help.className='provider-help';picker.after(help);
    const priority=document.createElement('div');priority.className='model-priorities';
    priority.innerHTML='<span>Prioritas model</span><div class="priority-buttons"><button type="button" data-model-priority="recommended">Rekomendasi</button><button type="button" data-model-priority="cheapest">Termurah</button><button type="button" data-model-priority="smartest">Paling pintar</button></div><p id="aiPriorityNote" class="field-help">Pilih provider, masukkan API key, lalu deteksi model. Termurah membandingkan harga yang tercatat; paling pintar merupakan saran keluarga model.</p><p id="aiModelDetail" role="status" class="model-price-detail"></p>';
    panel.append(priority);
    priority.querySelectorAll('button').forEach(button=>button.onclick=()=>{
      const id=discovered?.guidance?.[button.dataset.modelPriority];if(!id)return;
      const select=document.querySelector('#aiModel');if(![...select.options].some(o=>o.value===id))return;
      select.value=id;describe();priority.querySelectorAll('button').forEach(b=>b.setAttribute('aria-pressed',String(b===button)));
    });
    document.querySelector('#aiProvider').addEventListener('change',showProvider);
    document.querySelector('#aiModel').addEventListener('change',()=>{updateButtons();describe();});
    document.querySelector('#aiKey').addEventListener('input',()=>{discovered=null;document.querySelector('#aiModel').replaceChildren(new Option('Otomatis · saran provider','auto'));updateButtons();document.querySelector('#aiModelDetail').textContent='API key berubah. Deteksi ulang model untuk akun ini.';});
    showProvider();
  }
  return {init,models};
})();
