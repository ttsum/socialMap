module.exports = [
  { id: 'g-walk', activityId: 'a-walk', memberIds: ['u-lin', 'u-an', 'u-yu'] },
  { id: 'g-hike', activityId: 'a-hike', memberIds: ['u-an', 'u-qiao'] },
  { id: 'g-game', activityId: 'a-game', memberIds: ['u-yu', 'u-qiao', 'u-lin', 'u-an'] },
  { id: 'g-movie', activityId: 'a-movie', memberIds: ['u-qiao', 'u-an'] },
  { id: 'g-coffee', activityId: 'a-coffee', memberIds: ['u-lin', 'u-yu'] },
  { id: 'g-book', activityId: 'a-book', memberIds: ['u-qiao', 'u-yu', 'u-an'] }
].map(g => Object.assign(g, {
  hostUserId: g.memberIds[0],
  status: 'open',
  rules: ['提前 10 分钟到达集合点', '尊重彼此，加入后请在群里打个招呼', '行程有变时及时退出，让其他伙伴有机会加入']
}))
