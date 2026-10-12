// Compile every template/style independently with the local official compiler.
const fs = require('node:fs')
const path = require('node:path')
const { spawnSync } = require('node:child_process')
const root = path.resolve(__dirname, '..')
const compilerDir = process.argv[2]
if (!compilerDir) { console.error('Usage: node scripts/check-templates.js <directory containing wcc.exe and wcsc.exe> [--output <directory>]'); process.exit(1) }
const outputFlagIndex = process.argv.indexOf('--output')
const outputArg = outputFlagIndex === -1 ? '.qa' : process.argv[outputFlagIndex + 1]
if (!outputArg) { console.error('Missing value for --output'); process.exit(1) }
const files = []
function walk(dir) {
 for (const entry of fs.readdirSync(dir,{withFileTypes:true})) {
  if (['.qa','prototypes','docs','tests','scripts'].includes(entry.name)) continue
  const full=path.join(dir,entry.name)
  if(entry.isDirectory()) walk(full)
  else if(/\.(wxml|wxss)$/.test(entry.name)) files.push(path.relative(root,full).replace(/\\/g,'/'))
 }
}
walk(root)
const output=path.resolve(root, outputArg)
fs.mkdirSync(output,{recursive:true})
const report=[]
for (const file of files) {
 const kind=file.endsWith('.wxml')?'wxml':'wxss'
 const compiler=path.join(path.resolve(compilerDir),kind==='wxml'?'wcc.exe':'wcsc.exe')
 const target=path.join(output,file.replace(/\//g,'_')+'.compiled.js')
 const result=spawnSync(compiler,['-o',target,file],{cwd:root,encoding:'utf8'})
 const item={file,kind,status:result.status,stderr:result.stderr||'',error:result.error?result.error.message:null,outputBytes:fs.existsSync(target)?fs.statSync(target).size:0}
 report.push(item)
 // An empty WXSS (shared global styles only) may legitimately compile to 0 bytes.
 if(result.status!==0 || (kind==='wxml' && !item.outputBytes)) process.exitCode=1
}
for (const kind of ['wxml','wxss']) {
 const items=report.filter(r=>r.kind===kind)
 console.log(JSON.stringify({kind,files:items.length,passed:items.filter(r=>r.status===0).length,failures:items.filter(r=>r.status!==0)}))
}
fs.writeFileSync(path.join(output,'compiler-report.json'),JSON.stringify({checkedAt:new Date().toISOString(),report},null,2))
