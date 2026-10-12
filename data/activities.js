// 演示活动每次启动按下一次周六排期；金额、距离均为示例数据。
const base = new Date()
base.setHours(0, 0, 0, 0)
const days = (6 - base.getDay() + 7) % 7
base.setDate(base.getDate() + (days || (new Date().getHours() >= 12 ? 7 : 0)))
function schedule(offset, hour) {
  const d = new Date(base)
  d.setDate(d.getDate() + offset)
  d.setHours(hour, 0, 0, 0)
  return d.getTime()
}
module.exports = [
  { id: 'a-walk', title: '橘子洲日落慢走', category: '户外', locationName: '橘子洲', address: '长沙市岳麓区橘子洲景区入口', lat: 28.185, lng: 112.960, distanceKm: 2.4, pricePerPerson: 0, capacity: 8, startTime: schedule(0, 16), durationHours: 2, tags: ['安静', '散步', '朋友聚会'], theme: 'mint', symbol: '洲', description: '沿江慢慢走，聊聊最近的小事。无需运动基础，按大家的步调出发。', meetingPoint: '景区入口游客指示牌旁' },
  { id: 'a-hike', title: '岳麓山轻徒步', category: '户外', locationName: '岳麓山', address: '长沙市岳麓区登高路岳麓山东门', lat: 28.181, lng: 112.942, distanceKm: 4.8, pricePerPerson: 20, capacity: 10, startTime: schedule(0, 9), durationHours: 3, tags: ['徒步', '运动', '朋友聚会'], theme: 'yellow', symbol: '山', description: '走一条轻松的山间路线，途中留出拍照和休息时间。请穿舒适的运动鞋。', meetingPoint: '岳麓山东门广场' },
  { id: 'a-game', title: '湘江边桌游小聚', category: '桌游', locationName: '湘江中路', address: '长沙市天心区湘江中路（演示场地）', lat: 28.186, lng: 112.972, distanceKm: 1.8, pricePerPerson: 58, capacity: 8, startTime: schedule(0, 14), durationHours: 3, tags: ['桌游', '热闹', '朋友聚会'], theme: 'lilac', symbol: '趣', description: '从简单的破冰桌游开始，新手也可以加入。活动费用为演示估算，不产生实际订单。', meetingPoint: '场地一层接待区' },
  { id: 'a-movie', title: '五一广场观影局', category: '观影', locationName: '五一广场', address: '长沙市芙蓉区五一广场（演示影院）', lat: 28.195, lng: 112.977, distanceKm: 1.2, pricePerPerson: 45, capacity: 6, startTime: schedule(1, 19), durationHours: 2, tags: ['观影', '安静'], theme: 'peach', symbol: '映', description: '一起看场电影，再交换彼此的观影感受。影片与场次仅用于演示，未预订座位。', meetingPoint: '影院大厅海报墙旁' },
  { id: 'a-coffee', title: '梅溪湖咖啡闲聊', category: '咖啡', locationName: '梅溪湖', address: '长沙市岳麓区梅溪湖路（演示咖啡店）', lat: 28.191, lng: 112.909, distanceKm: 8.6, pricePerPerson: 38, capacity: 8, startTime: schedule(0, 15), durationHours: 2, tags: ['咖啡', '安静', '朋友聚会'], theme: 'mint', symbol: '叙', description: '带一本最近在看的书，或者只带一个想分享的故事。饮品预算按人均估算。', meetingPoint: '湖边咖啡店门口' },
  { id: 'a-book', title: '城南书店阅读时光', category: '阅读', locationName: '天心阁附近', address: '长沙市天心区城南路（演示书店）', lat: 28.179, lng: 112.978, distanceKm: 3.1, pricePerPerson: 25, capacity: 8, startTime: schedule(0, 14), durationHours: 2, tags: ['阅读', '安静', '朋友聚会'], theme: 'yellow', symbol: '阅', description: '先各自读一会儿，再分享喜欢的段落。不设主题，也不用提前准备。', meetingPoint: '书店一层阅读区' }
].map(item => Object.assign({ city: '长沙' }, item))
