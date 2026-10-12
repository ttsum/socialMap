const store = require('../../services/store')
const ai = require('../../data/mock-ai')
const { go, error } = require('../../utils/navigation')
Page({
 data: { intent: null, meta: null, days: ['不限', '周六', '周日'], periods: ['不限', '上午', '下午', '晚上'], dayIndex: 0, periodIndex: 0, preferenceText: '' },
 onLoad() { const saved = store.read(); const intent = saved.intent; if (!intent) return; this.setData({ intent, meta: saved.intentMeta || null, dayIndex: this.data.days.indexOf(intent.day), periodIndex: this.data.periods.indexOf(intent.period), preferenceText: (intent.preferences || []).join('、') }) },
 input(e) { const key = e.currentTarget.dataset.key; this.setData({ ['intent.' + key]: e.detail.value }) },
 preference(e) { this.setData({ preferenceText: e.detail.value }) },
 day(e) { const i = Number(e.detail.value); this.setData({ dayIndex: i, 'intent.day': this.data.days[i] }) },
 period(e) { const i = Number(e.detail.value); this.setData({ periodIndex: i, 'intent.period': this.data.periods[i] }) },
 submit() {
   const intent = Object.assign({}, this.data.intent)
   const invalid = ai.validate(intent)
   if (invalid) return error(new Error(invalid))
   intent.people = Number(intent.people); intent.maxDistanceKm = Number(intent.maxDistanceKm); intent.budgetPerPerson = Number(intent.budgetPerPerson)
   intent.preferences = this.data.preferenceText.split(/[、,，\s]+/).filter(Boolean)
   store.update(s => { s.intent = intent })
   go('matches')
 },
 publish() { go('publish') }
})
