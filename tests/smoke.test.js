const test = require('node:test')
const assert = require('node:assert/strict')
const fs = require('node:fs')
const path = require('node:path')
const vm = require('node:vm')
const root = path.resolve(__dirname, '..')
let storage = {}
let routes = []
let modals = []
let toasts = []
let acceptModal = true
global.getApp = () => ({ globalData: { mode: 'local-demo' } })
global.wx = {
 getStorageSync: k => storage[k] ? JSON.parse(JSON.stringify(storage[k])) : '',
 setStorageSync: (k, v) => { storage[k] = JSON.parse(JSON.stringify(v)) },
 showModal: o => { modals.push(o); if (o.success) o.success({ confirm: acceptModal, cancel: !acceptModal }) },
 showToast: o => toasts.push(o),
 switchTab: o => routes.push({ type: 'tab', url: o.url }),
 navigateTo: o => routes.push({ type: 'push', url: o.url }),
 redirectTo: o => routes.push({ type: 'replace', url: o.url }),
 setNavigationBarTitle: () => {}
}
const store = require('../services/store')
const ai = require('../data/mock-ai')
const activities = require('../data/activities')
const groups = require('../data/groups')
function reset() { storage = {}; routes = []; modals = []; toasts = []; acceptModal = true }
function page(name, options) {
 let definition
 global.Page = p => { definition = p }
 const file = path.join(root, 'pages', name, name + '.js')
 delete require.cache[require.resolve(file)]
 require(file)
 const p = Object.assign({}, definition)
 p.data = JSON.parse(JSON.stringify(definition.data))
 p.setData = values => {
  for (const [key, value] of Object.entries(values)) {
   const parts = key.split('.')
   let obj = p.data
   for (const part of parts.slice(0, -1)) obj = obj[part]
   obj[parts[parts.length - 1]] = value
  }
 }
 if (p.onLoad) p.onLoad(options || {})
 if (p.onShow) p.onShow()
 return p
}
test('nine complete pages, five tab routes, component and AppID', () => {
 const app = require('../app.json')
 assert.equal(app.pages.length, 9)
 assert.equal(new Set(app.pages).size, 9)
 assert.equal(app.tabBar.list.length, 5)
 assert.equal(require('../project.config.json').appid, 'wxcabe02fe45ec7f3c')
 for (const route of app.pages) for (const ext of ['js','json','wxml','wxss']) assert.ok(fs.existsSync(path.join(root, route + '.' + ext)))
 for (const tab of app.tabBar.list) {
  assert.ok(app.pages.includes(tab.pagePath))
  for (const asset of [tab.iconPath, tab.selectedIconPath]) {
    const image=fs.readFileSync(path.join(root,asset))
    assert.equal(image.readUInt32BE(16),81);assert.equal(image.readUInt32BE(20),81)
    assert.ok(image.length<40000)
  }
 }
 const ignored=require('../project.config.json').packOptions.ignore.map(x=>x.value)
 for(const value of ['prototypes','docs','tests','scripts','.qa']) assert.ok(ignored.includes(value))
 assert.ok(app.tabBar.list.some(t => t.pagePath === 'pages/messages/messages'))
 assert.ok(!app.tabBar.list.some(t => t.pagePath === 'pages/chat/chat'))
 assert.ok(fs.existsSync(path.join(root, app.usingComponents['activity-card'] + '.js')))
})
test('JS syntax, JSON parsing and WXML event handlers', () => {
 reset()
 function visit(dir) {
  for(const entry of fs.readdirSync(dir, {withFileTypes:true})) {
   if (['tests', 'docs', 'prototypes', '.qa', 'backend', 'node_modules'].includes(entry.name)) continue
   const f = path.join(dir,entry.name)
   if(entry.isDirectory()) visit(f)
   else if(f.endsWith('.json')) JSON.parse(fs.readFileSync(f,'utf8'))
   else if(f.endsWith('.js')) new vm.Script(fs.readFileSync(f,'utf8'), {filename:f})
  }
 }
 visit(root)
 for(const name of ['index','map','publish','confirm','matches','detail','messages','chat','profile']) {
  const p = page(name)
  const wxml = fs.readFileSync(path.join(root,'pages',name,name+'.wxml'),'utf8')
  for(const match of wxml.matchAll(/(?:bind|catch):?[a-z-]+="([A-Za-z]\w*)"/g)) assert.equal(typeof p[match[1]],'function',name+': '+match[1])
 }
})
test('default natural language finds four-person quiet Saturday afternoon plans', () => {
 reset()
 const intent = ai.parse(ai.DEFAULT_QUERY)
 assert.equal(intent.people, 4); assert.equal(intent.maxDistanceKm,5); assert.equal(intent.budgetPerPerson,100)
 assert.equal(intent.day,'周六'); assert.equal(intent.period,'下午'); assert.equal(ai.validate(intent),'')
 const results = store.recommend(intent)
 assert.ok(results.length >= 2)
 assert.ok(results.some(a => a.id === 'a-walk'))
 for(const a of results) {
  assert.ok(a.remaining >= 4 && a.distanceKm <= 5 && a.pricePerPerson <= 100)
  assert.equal(new Date(a.startTime).getDay(),6)
  assert.ok(new Date(a.startTime).getHours() >=12 && new Date(a.startTime).getHours() <18)
  assert.ok(a.reason.includes(String(a.distanceKm)))
 }
})
test('numerals, explicit totals, unknown date notes and invalid values', () => {
 reset()
 assert.equal(ai.parse('我们三个人，周六上午，五公里内，人均50元').people,3)
 assert.equal(ai.parse('和2位朋友').people,3)
 assert.ok(ai.parse('明天下午').notes.length > 1)
 assert.ok(ai.parse('明天下午').uncertainFields.includes('day'))
 for(const change of [{people:0},{people:1.5},{people:21},{maxDistanceKm:0},{maxDistanceKm:'abc'},{budgetPerPerson:-1},{budgetPerPerson:''}]) assert.ok(ai.validate(Object.assign(ai.parse(ai.DEFAULT_QUERY),change)))
})
test('budget, city, capacity, distance, day and time are hard constraints', () => {
 reset()
 const base = ai.parse(ai.DEFAULT_QUERY)
 assert.equal(store.recommend(Object.assign({},base,{city:'上海'})).length,0)
 assert.equal(store.recommend(Object.assign({},base,{maxDistanceKm:.1})).length,0)
 assert.equal(store.recommend(Object.assign({},base,{people:20})).length,0)
 const free = store.recommend(Object.assign({},base,{budgetPerPerson:0}))
 assert.ok(free.length); assert.ok(free.every(a=>a.pricePerPerson===0))
 const sunday = store.recommend(Object.assign({},base,{people:2,day:'周日',period:'晚上'}))
 assert.deepEqual(sunday.map(a=>a.id),['a-movie'])
 assert.equal(store.recommend(Object.assign({},base,{day:'周日',period:'上午'})).length,0)
})
test('activity IDs and group/member references are consistent', () => {
 reset()
 assert.equal(new Set(activities.map(a=>a.id)).size,activities.length)
 for(const g of groups) {
  const detail=store.getGroup(g.id)
  assert.ok(detail.activity && detail.members.every(Boolean))
  assert.equal(detail.activity.groupId,g.id)
  assert.ok(detail.activity.capacity>=detail.members.length)
 }
})
test('joining is authorized, idempotent and validates remaining seats', () => {
 reset()
 assert.throws(()=>store.join('g-walk',1),/演示身份/)
 store.login()
 assert.throws(()=>store.join('missing',1),/不存在/)
 assert.throws(()=>store.join('g-walk',6),/名额/)
 assert.throws(()=>store.join('g-walk',0),/名额/)
 store.join('g-walk',4)
 assert.equal(store.getActivity('a-walk').remaining,1)
 assert.equal(store.getActivity('a-walk').joinedCount,7)
 store.join('g-walk',4)
 assert.equal(store.getActivity('a-walk').joinedCount,7)
 store.leave('g-walk')
 assert.equal(store.getActivity('a-walk').remaining,5)
})
test('favorites, messages and joined state survive logout and reload', () => {
 reset();store.login();store.toggleFavorite('a-walk');store.join('g-walk',2)
 store.send('g-walk','  周末见  ')
 assert.equal(store.messages('g-walk').at(-1).content,'周末见')
 assert.throws(()=>store.send('g-walk',' '),/消息/)
 assert.throws(()=>store.send('g-walk','x'.repeat(501)),/消息/)
 assert.throws(()=>store.send('g-book','hi'),/先加入/)
 store.logout()
 assert.equal(store.conversations().length,0)
 assert.throws(()=>store.send('g-walk','hi'),/先加入/)
 store.login()
 assert.equal(store.conversations().length,1)
 assert.ok(store.getActivity('a-walk').favorite)
 assert.equal(store.getActivity('a-walk').joinedSeats,2)
 const file = require.resolve('../services/store')
 delete require.cache[file]
 assert.equal(require(file).messages('g-walk').at(-1).content,'周末见')
 store.toggleFavorite('a-walk');assert.equal(store.getActivity('a-walk').favorite,false)
})
test('canceling demo login leaves state unchanged', () => {
 reset();acceptModal=false
 let called=false;store.requireLogin(()=>{called=true})
 assert.equal(called,false);assert.equal(store.read().loggedIn,false)
})
test('full page flow: publish → confirm → matches → detail → chat → messages/profile', () => {
 reset()
 const home=page('index');assert.equal(home.data.activities.length,6);home.publish()
 assert.equal(routes.at(-1).url,'/pages/publish/publish')
 const publish=page('publish')
 publish.example({currentTarget:{dataset:{index:0}}});publish.submit()
 assert.equal(routes.at(-1).url,'/pages/confirm/confirm')
 const confirm=page('confirm');confirm.submit()
 assert.equal(routes.at(-1).url,'/pages/matches/matches')
 const matches=page('matches');matches.open({detail:{id:'a-walk'}})
 assert.ok(routes.at(-1).url.includes('people=4'))
 const detail=page('detail',{id:'a-walk',people:'4',source:'matches'})
 detail.join();assert.equal(routes.at(-1).url,'/pages/chat/chat?groupId=g-walk')
 assert.equal(store.getActivity('a-walk').joinedSeats,4)
 const chat=page('chat',{groupId:'g-walk'});assert.ok(chat.data.allowed)
 chat.input({detail:{value:'大家好，周末见！'}});chat.send()
 assert.equal(chat.data.messages.at(-1).content,'大家好，周末见！')
 const messages=page('messages');assert.equal(messages.data.conversations.length,1)
 detail.favorite()
 const profile=page('profile');assert.equal(profile.data.joined.length,1);assert.equal(profile.data.favorites.length,1)
 home.onShow();assert.equal(home.data.joinedCount,1)
 const map=page('map');assert.equal(map.data.activities.find(a=>a.id==='a-walk').remaining,1)
 detail.leave();messages.onShow();profile.onShow()
 assert.equal(messages.data.conversations.length,0);assert.equal(profile.data.joined.length,0)
})
test('confirmation edits actually affect matching and invalid input stays on page', () => {
 reset();store.update(s=>{s.intent=ai.parse(ai.DEFAULT_QUERY)})
 const confirm=page('confirm')
 confirm.input({currentTarget:{dataset:{key:'people'}},detail:{value:'0'}});confirm.submit()
 assert.equal(routes.length,0);assert.equal(toasts.length,1)
 confirm.input({currentTarget:{dataset:{key:'people'}},detail:{value:'2'}})
 confirm.day({detail:{value:2}});confirm.period({detail:{value:3}});confirm.submit()
 const results=page('matches');assert.deepEqual(results.data.activities.map(a=>a.id),['a-movie'])
})
test('invalid IDs, direct chat entry, empty results and guest profile are safe', () => {
 reset()
 assert.equal(page('detail',{id:'missing'}).data.activity,null)
 assert.equal(page('chat',{groupId:'missing'}).data.allowed,false)
 assert.equal(page('chat',{groupId:'g-walk'}).data.allowed,false)
 assert.equal(page('matches').data.activities.length,0)
 assert.equal(page('confirm').data.intent,null)
 assert.equal(page('profile').data.loggedIn,false)
 const publish=page('publish');publish.submit();assert.equal(routes.length,0)
})
test('category filtering and map marker selection', () => {
 reset()
 const home=page('index');home.selectCategory({currentTarget:{dataset:{value:'户外'}}})
 assert.equal(home.data.activities.length,2)
 const map=page('map');map.selectCategory({currentTarget:{dataset:{value:'咖啡'}}})
 assert.equal(map.data.pins.length,1);assert.equal(map.data.selected.id,'a-coffee')
 map.selectCategory({currentTarget:{dataset:{value:'全部'}}})
 map.selectPin({currentTarget:{dataset:{id:'a-book'}}})
 assert.equal(map.data.selected.id,'a-book')
})
test('activities that have started cannot be recommended or joined', () => {
 reset();store.login()
 const a=activities.find(a=>a.id==='a-walk');const previous=a.startTime
 try {a.startTime=Date.now()-1;assert.ok(!store.recommend(ai.parse(ai.DEFAULT_QUERY)).some(a=>a.id==='a-walk'));assert.throws(()=>store.join('g-walk',1),/已经开始/)}
 finally {a.startTime=previous}
})
