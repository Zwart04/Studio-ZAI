/* Visible creator controls backed by the same timeline used for export. */
const StudioFinishing = (() => {
  const presets = [['viral_yellow','Hook kuning'],['yellow_label','Kartu kuning'],['clean','Minimal'],['cyan_neon','Neon']];
  function dialog(title, body) {
    const el=document.createElement('dialog');el.className='creator-dialog';
    el.innerHTML=`<header><h2>${title}</h2><button data-close aria-label="Tutup">×</button></header>${body}<p class="finishing-status" role="status"></p>`;
    document.body.append(el);el.showModal();
    const close=()=>{el.close();el.remove();};el.querySelector('[data-close]').onclick=close;
    el.addEventListener('cancel',e=>{e.preventDefault();close();});return {el,close};
  }
  async function commit(editor,el,close) {
    try {await editor.save(true);editor.renderAll();editor.schedulePreview();close();}
    catch(e){el.querySelector('.finishing-status').textContent=e.message;}
  }
  function title(editor) {
    const existing=editor.items('text').find(i=>i.id==='creator_title');
    const {el,close}=dialog('Judul pembuka',`<p>Judul tampil di atas video pada awal klip. Teks dan preset dapat diubah.</p><label>Judul<textarea id="openingTitle" rows="3">${escapeHtml(existing?.text||editor.clip.title||'')}</textarea></label><button id="suggestTitle" class="ghost">Buat judul dari ucapan</button><label>Preset<select id="openingPreset">${presets.map(([id,label])=>`<option value="${id}">${label}</option>`).join('')}</select></label><div class="grid-2"><label>Durasi (detik)<input id="openingDuration" type="number" min=".2" max="${editor.duration()}" step=".1" value="${Math.min(existing?.end||3,editor.duration())}"></label><label>Ukuran font<input id="openingSize" type="number" min="14" max="160" value="${existing?.fontSize||86}"></label><label>X (%)<input id="openingX" type="number" min="5" max="95" value="${(existing?.x??.5)*100}"></label><label>Y (%)<input id="openingY" type="number" min="5" max="95" value="${(existing?.y??.16)*100}"></label></div><footer><button id="removeTitle" class="ghost">Hapus judul</button><button id="saveTitle" class="primary">Terapkan judul</button></footer>`);
    const q=id=>el.querySelector('#'+id);q('openingPreset').value=existing?.template||'viral_yellow';
    q('suggestTitle').onclick=()=>{const rows=editor.clip.captions||[];const row=rows.find(r=>/\?|kenapa|bagaimana|rahasia|why|how/i.test(r.text))||rows[0];q('openingTitle').value=(row?.text||editor.clip.title||'Momen pilihan').split(/\s+/).slice(0,12).join(' ');};
    q('removeTitle').onclick=()=>{editor.track('text').items=editor.items('text').filter(i=>i.id!=='creator_title');commit(editor,el,close);};
    q('saveTitle').onclick=()=>{const text=q('openingTitle').value.trim();if(!text)return;editor.track('text').items=editor.items('text').filter(i=>i.id!=='creator_title');editor.track('text').items.push({id:'creator_title',type:'text',text,template:q('openingPreset').value,start:0,end:Math.max(.2,Math.min(editor.duration(),+q('openingDuration').value||3)),x:Math.max(.05,Math.min(.95,+q('openingX').value/100)),y:Math.max(.05,Math.min(.95,+q('openingY').value/100)),fontSize:Math.max(14,Math.min(160,+q('openingSize').value||86)),opacity:1});editor.clip.title=text;commit(editor,el,close);};
  }
  function watermark(editor) {
    const old=editor.items('text').concat(editor.items('media')).find(i=>i.id==='creator_watermark');let src=old?.src||'';
    const {el,close}=dialog('Watermark milikmu',`<p>Logo PNG transparan atau tulisan ditampilkan sepanjang klip.</p><label>Jenis<select id="watermarkKind"><option value="text">Tulisan</option><option value="image">Logo gambar</option></select></label><label>Tulisan<input id="watermarkText" value="${escapeHtml(old?.text||'@namamu')}"></label><label>Pilih logo<input id="watermarkFile" type="file" accept="image/png,image/jpeg,image/webp"></label><div class="grid-2"><label>Lebar logo (%)<input id="watermarkScale" type="number" min="5" max="70" value="${(old?.scale||.18)*100}"></label><label>Ukuran font<input id="watermarkSize" type="number" min="14" max="160" value="${old?.fontSize||38}"></label><label>X (%)<input id="watermarkX" type="number" min="0" max="100" value="${(old?.x??.85)*100}"></label><label>Y (%)<input id="watermarkY" type="number" min="0" max="100" value="${(old?.y??.1)*100}"></label></div><label>Opacity (%)<input id="watermarkOpacity" type="range" min="5" max="100" value="${(old?.opacity??.75)*100}"></label><footer><button id="removeWatermark" class="ghost">Hapus watermark</button><button id="saveWatermark" class="primary">Terapkan watermark</button></footer>`);
    const q=id=>el.querySelector('#'+id);q('watermarkKind').value=old?.type==='image'?'image':'text';
    const remove=()=>['text','media'].forEach(k=>editor.track(k).items=editor.items(k).filter(i=>i.id!=='creator_watermark'));
    q('removeWatermark').onclick=()=>{remove();commit(editor,el,close);};
    q('saveWatermark').onclick=async()=>{const button=q('saveWatermark');button.disabled=true;try{
      const kind=q('watermarkKind').value;
      if(kind==='image'&&q('watermarkFile').files[0]){const file=q('watermarkFile').files[0];const response=await fetch(`/api/projects/${state.project.id}/assets-upload`,{method:'POST',headers:{'x-filename':encodeURIComponent(file.name)},body:file});const result=await response.json();if(!response.ok)throw new Error(result.detail||'Logo gagal diimpor');src=result.path;}
      if(kind==='image'&&!src)throw new Error('Pilih gambar logo terlebih dahulu.');
      if(kind==='text'&&!q('watermarkText').value.trim())throw new Error('Isi tulisan watermark.');
      remove();editor.track(kind==='text'?'text':'media').items.push({id:'creator_watermark',type:kind,start:0,end:editor.duration(),src,text:q('watermarkText').value.trim(),template:'clean',fontSize:Math.max(14,Math.min(160,+q('watermarkSize').value||38)),scale:Math.max(.05,Math.min(.7,+q('watermarkScale').value/100)),opacity:+q('watermarkOpacity').value/100,x:Math.max(0,Math.min(1,+q('watermarkX').value/100)),y:Math.max(0,Math.min(1,+q('watermarkY').value/100))});await commit(editor,el,close);
    }catch(e){el.querySelector('.finishing-status').textContent=e.message;}finally{button.disabled=false;}};
  }
  return {title,watermark};
})();
