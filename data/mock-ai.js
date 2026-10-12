const numerals = { '一': 1, '两': 2, '二': 2, '三': 3, '四': 4, '五': 5, '六': 6, '七': 7, '八': 8, '九': 9, '十': 10 }
function number(text) { return numerals[text] || Number(text) }
const DEFAULT_QUERY = '周六下午和三位朋友，找长沙市区五公里内、人均100元以内、安静一点的活动'
function parse(query) {
  const q = query.trim()
  const notes = ['当前使用本地规则解析，请确认人数、日期和预算；尚未识别的条件不会自动参与筛选。']
  const uncertainFields = []
  const companion = q.match(/(?:和|带上|带)([一二两三四五六七八九十\d]+)(?:位|个)?朋友/)
  const total = q.match(/(?:一共|共|我们)?([一二两三四五六七八九十\d]+)(?:个人|人)/)
  const distance = q.match(/([一二两三四五六七八九十\d.]+)\s*(?:公里|千米|km)/i)
  const budget = q.match(/(?:人均|预算)[^\d]{0,4}(\d+(?:\.\d+)?)\s*(?:元|块)?/)
  const preferences = ['安静', '热闹', '徒步', '散步', '桌游', '观影', '咖啡', '阅读'].filter(x => q.indexOf(x) >= 0)
  if (/朋友/.test(q)) preferences.push('朋友聚会')
  const people = companion ? number(companion[1]) + 1 : total ? number(total[1]) : 1
  const day = /周日|星期日|星期天/.test(q) ? '周日' : /周六|星期六/.test(q) ? '周六' : '不限'
  const period = /下午/.test(q) ? '下午' : /晚上|晚间/.test(q) ? '晚上' : /上午|早上/.test(q) ? '上午' : '不限'
  if (/今天|明天|后天|下周|下星期|周[一二三四五]|星期[一二三四五]|\d+月|\d+[号日]|\d+[:：点]/.test(q)) { notes.push('检测到具体日期或时刻，规则演示无法完整解析，请手动选择活动日期和时段。'); uncertainFields.push('day') }
  if (/不想|不要|不喜欢|不超过|至少|最少|除了/.test(q)) { notes.push('检测到否定或比较表达，请核对筛选条件，偏好仅用于排序。'); uncertainFields.push('preferences') }
  if (!budget) { notes.push('未识别人均预算，暂用 100 元，请按需要修改。'); uncertainFields.push('budgetPerPerson') }
  if (!distance) { notes.push('未识别距离范围，暂用 5 公里。距离以示例位置计算。'); uncertainFields.push('maxDistanceKm') }
  if (period === '不限') uncertainFields.push('period')
  return { query: q, people: Number.isFinite(people) ? people : 1, day, period, maxDistanceKm: distance ? number(distance[1]) : 5, budgetPerPerson: budget ? Number(budget[1]) : 100, preferences, city: '长沙', notes, uncertainFields: Array.from(new Set(uncertainFields)) }
}
function validate(intent) {
  if (!intent || !Number.isInteger(Number(intent.people)) || intent.people < 1 || intent.people > 20) return '同行总人数请填写 1 至 20 的整数'
  if (!Number.isFinite(Number(intent.maxDistanceKm)) || Number(intent.maxDistanceKm) <= 0 || Number(intent.maxDistanceKm) > 100) return '距离请填写大于 0、至多 100 公里'
  if (!Number.isFinite(Number(intent.budgetPerPerson)) || intent.budgetPerPerson === '' || Number(intent.budgetPerPerson) < 0 || intent.budgetPerPerson > 10000) return '人均预算请填写 0 至 10000 元'
  if (['不限', '周六', '周日'].indexOf(intent.day) < 0 || ['不限', '上午', '下午', '晚上'].indexOf(intent.period) < 0) return '请选择有效日期和时段'
  return ''
}
module.exports = { parse, validate, DEFAULT_QUERY }
