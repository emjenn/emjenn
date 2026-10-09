const { chromium } = require('playwright'); const path=require('path');
(async()=>{const b=await chromium.launch({args:['--allow-file-access-from-files']});const p=await b.newPage({viewport:{width:1920,height:1080}});
await p.goto('file://'+path.resolve('motion.html'));await p.evaluate(()=>window.ready);
console.log(await p.evaluate(()=>{const cnt=m=>{const d=m.getImageData(0,0,m.canvas.width,m.canvas.height).data;let n=0;for(let i=3;i<d.length;i+=4)if(d[i])n++;return n};
const c=document.createElement('canvas');c.width=900;c.height=640;const m=c.getContext('2d');
const r=[];for(const f of ['900 640px IDBlack','900 300px IDBlack','900 640px sans-serif']){m.clearRect(0,0,900,640);m.font=f;m.fillStyle='#fff';m.textAlign='center';m.textBaseline='middle';m.fillText('10',450,340);r.push(f+':'+cnt(m)+':'+m.font);}return r;}));
await b.close();})();
