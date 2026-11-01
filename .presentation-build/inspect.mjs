import fs from 'node:fs/promises';
import {PresentationFile,FileBlob} from '@oai/artifact-tool';
const p=await PresentationFile.importPptx(await FileBlob.load('/Users/redasbai/.codex/plugins/cache/openai-curated-remote/openai-templates/0.1.1/skills/artifact-template-project-kickoff/assets/reference.pptx'));
await fs.writeFile('.presentation-build/source-inspect.jsonl',(await p.inspect({kind:'slide,textbox,shape,image,layout',maxChars:100000})).ndjson);
for(let i=0;i<p.slides.items.length;i++){
 const slide=p.slides.items[i];
 await fs.writeFile(`.presentation-build/source-${i+1}.png`,new Uint8Array(await (await slide.export({format:'png',scale:1})).arrayBuffer()));
 await fs.writeFile(`.presentation-build/source-${i+1}.json`,await (await slide.export({format:'layout'})).text());
}
console.log('slides',p.slides.items.length);
