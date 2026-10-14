const SubtitleOverlay = (() => {
  const fonts = ['Inter', 'Anton', 'Barlow Condensed', 'DM Serif Display', 'Kalam'];
  const clamp = (value, fallback, low, high) => Number.isFinite(Number(value)) ? Math.max(low, Math.min(high, Number(value))) : fallback;
  const color = (value, fallback) => /^#[\da-f]{6}$/i.test(String(value)) ? value : fallback;
  function words(cue) {
    if (cue.words?.length) return cue.words;
    const tokens = String(cue.text || '').trim().split(/\s+/).filter(Boolean);
    return tokens.map((word, i) => ({word, start:cue.start + (cue.end-cue.start)*i/tokens.length,
      end:cue.start + (cue.end-cue.start)*(i+1)/tokens.length}));
  }
  function previewWords(cue, time) {
    const all = words(cue).filter(row => Number.isFinite(row.start) && Number.isFinite(row.end) && row.end > row.start);
    const mode = cue.style?.mode || 'line';
    if (mode === 'word' || mode === 'box') return all.filter(row => row.start <= time && time < row.end);
    if (mode !== 'highlight') return all;
    const chunks = []; let current = [], chars = 0;
    all.forEach(row => {
      const token = String(row.word), last = current[current.length-1];
      if (current.length >= 3 || last && (row.start-last.end >= .38 || /[.!?]$/.test(last.word) || chars+token.length > 22)) {
        chunks.push(current); current = []; chars = 0;
      }
      current.push(row); chars += token.length+1;
    });
    if (current.length) chunks.push(current);
    const bounds = [];
    chunks.forEach(chunk => {
      let start = chunk[0].start, end = Math.max(start+.35, chunk[chunk.length-1].end+.12);
      if (bounds.length) { start = Math.max(start,bounds[bounds.length-1][1]); if (end <= start) end = start+.28; }
      bounds.push([start,end]);
    });
    for (let i=0; i<bounds.length-1; i++) {
      if (bounds[i][1] > bounds[i+1][0]) {
        const split = Math.max(bounds[i][0]+.28,bounds[i+1][0]); bounds[i][1]=split;
        if(bounds[i+1][0]<split){bounds[i+1][0]=split;bounds[i+1][1]=Math.max(split+.28,bounds[i+1][1]);}
      }
    }
    const index = bounds.findIndex(([s,e]) => Math.max(s,cue.start) <= time && time < Math.min(e,cue.end));
    if(index<0) return [];
    const chunk=chunks[index], [start,end]=bounds[index], points=[start];
    for(let i=1;i<chunk.length;i++){
      const low=points[i-1]+.16, high=end-.16*(chunk.length-i);
      points.push(low>high ? points[i-1]+(end-points[i-1])/(chunk.length-i+1) : Math.max(low,Math.min(high,chunk[i].start)));
    }
    points.push(Math.min(end,cue.end));
    return chunk.map((row,i)=>({...row,start:points[i],end:points[i+1]}));
  }
  function mount(frame, player, readClip, sourceStart) {
    const layer = document.createElement('div'); layer.className = 'live-subtitle'; layer.setAttribute('aria-hidden', 'true');
    frame.append(layer);
    const timing = document.createElement('small'); timing.className = 'subtitle-timing'; frame.append(timing);
    let cueId = null, spans = [], rows = [], raf = null;
    const paint = () => {
      const clip = readClip(), time = player.currentTime - sourceStart;
      const cue = clip.captions?.find(row => row.start <= time && time < row.end);
      layer.hidden = !cue || clip.subtitle_position === 'off';
      if (!cue || clip.subtitle_position === 'off') { timing.textContent = ''; return; }
      const style = cue.style || {}, visibleWords = previewWords(cue,time), id = JSON.stringify([cue,visibleWords]);
      if (id !== cueId) {
        cueId = id; rows = visibleWords; layer.replaceChildren();
        spans = rows.map(row => {const span = document.createElement('span'); span.textContent = row.word + ' '; layer.append(span); return span;});
        layer.dataset.timing = cue.timing_quality || (cue.words?.length ? 'platform/measured' : 'estimated');
        timing.textContent = layer.dataset.timing === 'estimated' ? 'Timing kata diperkirakan' : '';
        layer.title = cue.words?.length ? 'Timestamp kata dari sumber' : 'Timestamp kata diperkirakan';
      }
      layer.style.fontFamily = fonts.includes(style.font) ? style.font : 'Inter, sans-serif';
      layer.style.fontSize = `${Math.max(12, clamp(style.size,56,14,160) * frame.clientHeight / 1920)}px`;
      layer.style.fontWeight = style.bold ? '700' : '600';
      layer.style.left = `${clamp(style.x,.5,.05,.95) * 100}%`;
      layer.style.top = `${clamp(style.y,({top:.15,middle:.5,bottom:.82}[clip.subtitle_position] || .82),.05,.95) * 100}%`;
      rows.forEach((row, i) => {
        const span = spans[i], active = row.start <= time && time < row.end;
        const wordStyle = {...style, ...(row.style || {})};
        span.style.fontFamily = fonts.includes(wordStyle.font) ? wordStyle.font : layer.style.fontFamily;
        span.style.fontSize = `${Math.max(12, clamp(wordStyle.size,56,14,160) * frame.clientHeight / 1920)}px`;
        span.style.fontWeight = wordStyle.bold === false ? '400' : wordStyle.bold ? '700' : layer.style.fontWeight;
        const mode = style.mode || 'line', animation = row.style?.animation || style.animation || 'none';
        const age = Math.max(0, time-row.start), progress = Math.min(1, age/.22);
        span.style.visibility = mode === 'word' && !active || ['type','typewriter'].includes(animation) && time < row.start ? 'hidden' : 'visible';
        const normal = color(row.style?.color || style.color,'#ffffff'), highlight = color(style.highlight,'#abff66');
        span.style.color = active && ['highlight','box'].includes(mode) ? highlight : normal;
        span.style.background = active && mode === 'box' ? color(style.boxColor,'#111111') : 'transparent';
        span.style.backgroundClip = ''; span.style.webkitBackgroundClip = '';
        if(mode === 'karaoke'){
          const filled = clamp((time-row.start)/(row.end-row.start),0,0,1)*100;
          span.style.background = `linear-gradient(90deg,${highlight} ${filled}%,${normal} ${filled}%)`;
          span.style.backgroundClip='text';span.style.webkitBackgroundClip='text';span.style.color='transparent';
        }
        let scale = 1, scaleY = 1, y = 0, opacity = 1;
        if (active && animation === 'pop') scale = age < .13 ? .75 + Math.min(1,age/.13)*.33 : 1.08 - Math.min(1,(age-.13)/.09)*.08;
        if (active && animation === 'bounce') scaleY = age < .1 ? .7 + age*5 : 1.2 - Math.min(1,(age-.1)/.12)*.2;
        if (active && animation === 'rise') y = (1-progress)*8;
        if (active && animation === 'zoom') scale = .85 + progress*.15;
        if (active && animation === 'fade') opacity = progress;
        span.style.transform = `translateY(${y}px) scale(${scale},${scale*scaleY})`; span.style.opacity = String(opacity);
      });
    };
    const tick = () => {paint(); if (!player.paused) raf = requestAnimationFrame(tick);};
    const play = () => {cancelAnimationFrame(raf); tick();};
    player.addEventListener('play', play); player.addEventListener('seeked', paint); player.addEventListener('timeupdate', paint);
    paint();
    return {paint, destroy(){cancelAnimationFrame(raf);player.removeEventListener('play',play);player.removeEventListener('seeked',paint);player.removeEventListener('timeupdate',paint);layer.remove();timing.remove();}};
  }
  return {mount, words, previewWords};
})();
