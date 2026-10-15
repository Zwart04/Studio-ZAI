const LiveTimeline = (() => {
  function style(p){return p?{font:p.font,size:Number(p.size||76),color:p.color,bold:p.bold!==false,italic:p.italic==='yes',outlineColor:p.outline,box:p.box==='yes',mode:p.karaoke?'karaoke':'line',animation:'none'}:{};}
  function mount(frame,player,editor){
    const entries=new Map();let raf=null,last=0;
    const canvas=document.createElement('canvas'),toggle=document.createElement('button');
    canvas.className='live-framing';toggle.className='live-play';toggle.type='button';toggle.textContent='Putar';
    toggle.onclick=()=>{if(player.paused)player.play().catch(()=>{});else player.pause();};frame.append(canvas,toggle);
    const ctx=canvas.getContext('2d');
    const offset=()=>Number(player.dataset.sourceStart||0);
    function paint(){
      const time=player.currentTime-offset(), wanted=new Set();
      const base=editor.items('video')[0]||{}, special=['manual','split','blur'].includes(base.crop);
      canvas.hidden=!special;toggle.hidden=true;player.controls=false;
      if(special&&player.readyState>=2){
        const w=Math.max(2,Math.min(640,Math.round(frame.clientWidth))),h=Math.max(2,Math.round(w/editor.stageRatio));
        if(canvas.width!==w||canvas.height!==h){canvas.width=w;canvas.height=h;}
        const sw=player.videoWidth,sh=player.videoHeight;
        const draw=(f,y,height)=>{
          const view=CreatorEditor.shiftFraming(f||{},Math.max(0,time),.1),zoom=Math.max(1,Math.min(4,view.zoom||1)),ratio=w/height;
          const cw=Math.min(sw,sh*ratio)/zoom,ch=Math.min(sh,sw/ratio)/zoom;
          const x=Math.max(0,Math.min(sw-cw,(view.x??.5)*sw-cw/2)),sy=Math.max(0,Math.min(sh-ch,(view.y??.5)*sh-ch/2));
          ctx.drawImage(player,x,sy,cw,ch,0,y,w,height);
        };
        ctx.clearRect(0,0,w,h);
        if(base.crop==='split'){const f=base.framing||{},height=h*Math.max(.2,Math.min(.8,f.fraction||.35));draw(f.top||{x:.15,y:.2,zoom:2},0,height);draw(f.bottom,height,h-height);}
        else if(base.crop==='blur'){ctx.filter='blur(12px)';draw({},0,h);ctx.filter='none';const scale=Math.min(w/sw,h/sh);ctx.drawImage(player,(w-sw*scale)/2,(h-sh*scale)/2,sw*scale,sh*scale);}
        else draw(base.framing,0,h);
      }
      for(const kind of ['text','media','audio'])for(const item of editor.items(kind)){
        const key=kind+':'+item.id;wanted.add(key);let entry=entries.get(key);
        if(entry && entry.src!==item.src){entry.destroy();entries.delete(key);entry=null;}
        if(!entry){
          if(kind==='text'){
            const overlay=SubtitleOverlay.mount(frame,player,()=>{
              const current=editor.items('text').find(row=>row.id===item.id)||item;
              return {subtitle_position:'middle',captions:[{start:current.start,end:current.end,text:current.text,
                style:{...style(editor.presets.find(p=>p.id===current.template)),...(current.fontSize?{size:current.fontSize}:{}),...current.style,mode:'overlay',opacity:current.opacity??1,x:current.x,y:current.y}}]};
            },offset,true);
            entry={src:item.src,paint:overlay.paint,destroy:overlay.destroy};
          }else{
            const node=document.createElement(kind==='audio'?'audio':item.type==='video'?'video':'img');
            node.className='live-timeline-asset';node.src=mediaUrl(item.src);node.draggable=false;
            if(node.tagName!=='IMG'){node.preload='metadata';node.playsInline=true;}
            frame.append(node);
            entry={src:item.src,node,destroy(){if(node.pause)node.pause();node.removeAttribute('src');node.remove();}};
          }
          entries.set(key,entry);
        }
        if(entry.paint){entry.paint();continue;}
        const node=entry.node,active=time>=item.start&&time<item.end;
        node.hidden=!active||kind==='audio';
        if(kind==='media'){
          node.style.left=`${Math.max(0,Math.min(1,item.x??.5))*100}%`;
          node.style.top=`${Math.max(0,Math.min(1,item.y??.5))*100}%`;
          node.style.width=`${Math.max(.05,Math.min(1,item.scale??.6))*100}%`;
          node.style.opacity=String(Math.max(0,Math.min(1,item.opacity??1)));
        }
        if(node.pause){
          node.volume=Math.max(0,Math.min(1,item.gain??(kind==='audio'?.6:0)));
          const at=Math.max(0,time-item.start+(item.srcStart||0));
          if(active&&Number.isFinite(node.duration)&&Math.abs(node.currentTime-at)>.25)node.currentTime=Math.min(at,node.duration);
          if(active&&!player.paused&&node.paused)node.play().catch(()=>{});
          if(!active||player.paused)node.pause();
        }
      }
      for(const [key,entry] of entries)if(!wanted.has(key)){entry.destroy();entries.delete(key);}
    }
    function tick(now){if(now-last>40){paint();last=now;}if(!player.paused)raf=requestAnimationFrame(tick);}
    function play(){cancelAnimationFrame(raf);raf=requestAnimationFrame(tick);}
    player.addEventListener('play',play);player.addEventListener('pause',paint);player.addEventListener('seeked',paint);paint();
    return {paint,destroy(){cancelAnimationFrame(raf);player.removeEventListener('play',play);player.removeEventListener('pause',paint);player.removeEventListener('seeked',paint);for(const e of entries.values())e.destroy();entries.clear();canvas.remove();toggle.remove();}};
  }
  return {mount,style};
})();
