// ===== helpers =====
async function jget(url){ const r=await fetch(url); if(!r.ok) throw new Error(`${r.status}`); return r.json(); }
async function jpost(url, body){ const r=await fetch(url,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)}); const t=await r.json().catch(()=>({})); if(!r.ok) throw Object.assign(new Error('HTTP '+r.status), {payload:t}); return t; }
const $ = id => document.getElementById(id);
const fmtNum = n => typeof n==='number' ? n.toLocaleString() : String(n);

// ===== tick period estimator (no backend changes) =====
const tickObs = [];
let estPeriod = 2; // seconds; will refine from frames
function observeTick(frame){
  tickObs.push({id: frame.tickId, t: frame.unixSeconds});
  if(tickObs.length > 6) tickObs.shift();
  if(tickObs.length >= 2){
    // median delta of unixSeconds between last frames
    const ds = [];
    for(let i=1;i<tickObs.length;i++) ds.push(tickObs[i].t - tickObs[i-1].t);
    ds.sort((a,b)=>a-b);
    const med = ds[Math.floor(ds.length/2)];
    if(med>=1 && med<=10) estPeriod = med;
  }
}

// ===== UI: Slots =====
function buildReel(el, finalDigit){
  // Build 0..9 then repeat final digit at end
  el.replaceChildren(); // clear
  for(let i=0;i<=9;i++){
    const d = document.createElement('div');
    d.className = 'digit ' + (i===finalDigit?'':'mut');
    d.textContent = i;
    el.appendChild(d);
  }
  // Append repeat so landing position is clean
  const tail = document.createElement('div');
  tail.className = 'digit';
  tail.textContent = finalDigit;
  el.appendChild(tail);
}

function spinReel(el, finalDigit, delayMs){
  buildReel(el, finalDigit);
  // Compute end offset: each digit 100px tall; we want last repeated slot in view
  el.style.setProperty('--end', `-${(10)*100}px`);
  el.style.setProperty('--dur', `${800 + delayMs}ms`);
  // trigger reflow
  void el.offsetWidth;
  el.classList.remove('spin');
  void el.offsetWidth;
  setTimeout(()=> el.classList.add('spin'), 10);
}

// ===== renderers =====
function setKV(target, data){
  const entries = Object.entries(data);
  target.replaceChildren();
  for(const [k,v] of entries){
    const kEl = document.createElement('div'); kEl.className='k'; kEl.textContent=k;
    const vEl = document.createElement('div'); vEl.className='v';
    if(Array.isArray(v) || typeof v === 'object'){
      const pre = document.createElement('pre'); pre.className='mono codebox'; pre.textContent = JSON.stringify(v, null, 2);
      vEl.appendChild(pre);
    } else {
      vEl.textContent = String(v);
    }
    target.append(kEl, vEl);
  }
}

function cardForFrame(f){
  const el = document.createElement('div');
  el.className = 'card';
  const h = document.createElement('h4');
  h.textContent = `tick ${f.tickId} • ${new Date(f.unixSeconds*1000).toLocaleTimeString()}`;
  const pre = document.createElement('pre');
  pre.className='mono';
  pre.textContent = JSON.stringify({
    reels: f.reels, jackpotPreview: f.jackpotPreview,
    sampleInts: f.sampleInts.slice(0,6), // shorten in cards
    sampleBytesHex: (f.sampleBytesHex||'').slice(0,8)+'…'
  }, null, 2);
  el.append(h, pre);
  return el;
}

// ===== state =====
let currentFrame = null;
let autoTimer = null;

// ===== main actions =====
async function loadCurrentFrame(manual=false){
  const data = await jget('/api/frame');
  currentFrame = data;

  // Observe tick & update header
  observeTick(data);
  $('tickStatus').textContent = `tick ${data.tickId} • ~${estPeriod}s period`;

  // Slot animation
  if(Array.isArray(data.reels) && data.reels.length===3){
    spinReel($('reel0'), data.reels[0], 0);
    spinReel($('reel1'), data.reels[1], 120);
    spinReel($('reel2'), data.reels[2], 240);
    // subtle highlight on update
    document.querySelectorAll('.slot').forEach(s=>{
      s.classList.add('updated');
      setTimeout(()=>s.classList.remove('updated'), 600);
    });
  }

  setKV($('frameTable'), {
    tickId: data.tickId,
    time: new Date(data.unixSeconds*1000).toLocaleString(),
    reels: data.reels,
    jackpotPreview: data.jackpotPreview,
    sampleInts_len: data.sampleInts?.length ?? 0,
    sampleBytes_hex_len: data.sampleBytesHex?.length ?? 0
  });

  // Prefill redeem tick: next one is a common move
  $('tickId').value = (data.tickId);
  if(manual){
    // if manual refresh, keep user's code
  } else {
    // clear outputs on fresh tick
    $('redeemOut').textContent = '—';
    $('flagHex').value = '';
  }
}

async function loadRecent(){
  const n = parseInt($('recentCount').value || '15', 10);
  const list = await jget(`/api/recent/${n}`);
  const container = $('recentList');
  container.replaceChildren();
  list.slice().reverse().forEach(f => container.appendChild(cardForFrame(f)));
}

async function doRedeem(){
  const tickId = parseInt($('tickId').value || '0', 10);
  const code = parseInt($('redeemCode').value || '0', 10);
  try{
    const res = await jpost('/api/redeem', { tickId, code });
    $('redeemOut').textContent = JSON.stringify(res, null, 2);
    $('flagHex').value = res.flag_xor_hex || '';
  }catch(e){
    $('redeemOut').textContent = JSON.stringify(e.payload || {error: e.message}, null, 2);
    $('flagHex').value = '';
  }
}

// ===== header countdown (no backend API; estimate from period & last frame) =====
setInterval(()=>{
  if(!currentFrame) return $('tickCountdown').textContent='—';
  const period = Math.max(1, estPeriod);
  const next = (currentFrame.unixSeconds + period) * 1000;
  const now = Date.now();
  const ms = Math.max(0, next - now);
  const s = (ms/1000).toFixed(1);
  $('tickCountdown').textContent = s + 's';
}, 100);

// ===== wire up =====
$('btnRefresh').onclick = ()=>loadCurrentFrame(true);
$('btnRecent').onclick = loadRecent;
$('btnRedeem').onclick = doRedeem;
$('btnUseNext').onclick = ()=>{
  if(currentFrame) $('tickId').value = (currentFrame.tickId + 1);
};
$('btnCopyFlag').onclick = ()=>{
  const v = $('flagHex').value || '';
  if(!v) return;
  navigator.clipboard.writeText(v).then(()=>{
    $('btnCopyFlag').textContent='Copied!';
    setTimeout(()=>$('btnCopyFlag').textContent='Copy', 800);
  });
};

// Auto-refresh logic: pull /api/frame slightly faster than period guess
function startAuto(){
  if(autoTimer) clearInterval(autoTimer);
  autoTimer = setInterval(()=>{
    // Pull slightly faster to catch new tick quickly
    loadCurrentFrame(false).catch(()=>{});
  }, Math.max(400, estPeriod*1000*0.66));
}
function stopAuto(){
  if(autoTimer) { clearInterval(autoTimer); autoTimer=null; }
}
$('autoRefresh').onchange = (e)=> e.target.checked ? startAuto() : stopAuto();

// First paint
loadCurrentFrame(false).then(loadRecent).then(startAuto).catch(console.error);
