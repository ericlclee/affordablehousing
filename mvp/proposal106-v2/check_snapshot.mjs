import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
const html = fs.readFileSync(new URL('index.html', import.meta.url), 'utf8');
const block = (a,b) => html.slice(html.indexOf(a),html.indexOf(b,html.indexOf(a)));
const engine = html.split('/* ENGINE-START */')[1].split('/* ENGINE-END */')[0];
const previous = fs.readFileSync(new URL('../proposal106/index.html',import.meta.url),'utf8').split('/* ENGINE-START */')[1].split('/* ENGINE-END */')[0];
assert.equal(engine,previous,'Reviewed arithmetic engine must stay unchanged');
const geometry = new Function(engine + '\n' + block('function ringOpen(', 'function LP(') + block('function convexHull(', 'function onUpload(') + '\nreturn {parseGeoJSON,applyUpload};')();
for (const coordinates of [ [[1,1],[1,1],[1,1],[1,1]], [[null,1],[2,2],[3,1],[null,1]], [[Infinity,1],[2,2],[3,1],[Infinity,1]] ]) {
  assert.throws(()=>geometry.parseGeoJSON({type:'Polygon',coordinates:[coordinates]},'invalid.json'));
}
const valid=geometry.parseGeoJSON({type:'Feature',properties:{height:12},geometry:{type:'Polygon',coordinates:[[[-.1,51.5],[-.099,51.5],[-.099,51.501],[-.1,51.5]]]}},'valid.json');
assert.ok(Number.isFinite(valid.area) && valid.area>0);
assert.equal(valid.height_m,12);
assert.throws(()=>geometry.applyUpload({area:0,ring:[[0,0],[0,0],[0,0]]}),/non-zero footprint/);
const verdict = new Function('flagLabel','trunc','f0',block('function verdictOf(', 'function flagsLine(')+';return verdictOf;')(()=>'',String,Math.round);
const base={stop:[],ser:[],sup:[],chk:[],tall:false,o:{affordable_hr_pct:35},r:{badge:'Fast Track'}};
for (const cstatus of ['error','loading','cached','idle']) assert.equal(verdict({...base,cstatus}).title,'Screening incomplete');
assert.equal(verdict({...base,cstatus:'ok',screeningIncomplete:true}).title,'Screening incomplete');
assert.equal(verdict({...base,cstatus:'ok'}).title,'Supportable in principle');
const layerCode=block('async function londonHit(', 'function cachedEnts(');
for (const response of [null,{error:{message:'unavailable'}},{}]) {
  const hit=new Function('timedJSON','isNum','TIER',layerCode+';return londonHit;')(async()=>{if(response===null)throw Error('offline');return response;},Number.isFinite,{CHECK:true});
  assert.equal((await hit({key:'test',url_template:'https://example.invalid/{lat}/{lng}'},51.5,-.1)).failed,true);
}
// Exercise provider UI handlers with fake credentials and mocked requests only.
const fields=new Map(),handlers=new Map(),requests=[];
const el=id=>{
  if(!fields.has(id)) fields.set(id,{value:'',textContent:'',hidden:true,className:'',addEventListener:(event,fn)=>handlers.set(id+':'+event,fn),replaceChildren(){this.value='';},appendChild(o){if(!this.value)this.value=o.value;},setAttribute(){},parentElement:{contains:()=>true}});
  return fields.get(id);
};
const store=new Map([['p106_ai_prov','groq'],['p106_ai_key','FAKE_TEST_KEY'],['p106_ai_model','test-model']]);
const context={window:{},document:{readyState:'loading',getElementById:el,createElement:()=>({value:'',textContent:''}),addEventListener:(n,f)=>handlers.set('document:'+n,f)},localStorage:{getItem:k=>store.get(k),setItem:(k,v)=>store.set(k,v),removeItem:k=>store.delete(k)},fetch:async(url,opt)=>{requests.push({url,opt});return {ok:true,json:async()=>({data:[{id:'qwen:free'}]})};},setTimeout:()=>{},console};
vm.runInNewContext(html.split('<script id="ai-connect">')[1].split('</script>')[0],context);
handlers.get('document:DOMContentLoaded')();
el('aiProv').value='openrouter';
handlers.get('aiProv:change')();
await handlers.get('aiLoad:click')();
assert.equal(requests.length,0,'Switching provider must not send a saved key elsewhere');
el('aiModel').value='old-model'; handlers.get('aiSave:click')();
assert.equal(store.get('p106_ai_prov'),'groq','Cannot save a new provider with old credentials');
el('aiProv').value='groq'; handlers.get('aiProv:change')();
await handlers.get('aiLoad:click')();
assert.equal(requests.length,1);
assert.ok(requests[0].url.startsWith('https://api.groq.com/'));
assert.equal(requests[0].opt.headers.Authorization,'Bearer FAKE_TEST_KEY');
const data=new URL('data/',import.meta.url);
const councils=JSON.parse(fs.readFileSync(new URL('councils.json',data),'utf8'));
const boroughs=JSON.parse(fs.readFileSync(new URL('london-boroughs.geojson',data),'utf8'));
for(const feature of boroughs.features) assert.ok(councils[feature.properties.name],feature.properties.name);
console.log('PASS: unchanged engine, valid/invalid uploads, incomplete screening, provider-key isolation, all council packs. No live AI requests.');
