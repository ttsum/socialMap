module.exports = function (group, activity) {
  return [
    { id: group.id + '-welcome', type: 'system', content: '欢迎来到' + activity.title + '。这里是本地演示群聊。' },
    { id: group.id + '-host', type: 'text', senderId: group.hostUserId, content: '欢迎加入！我们在' + activity.meetingPoint + '集合，有问题可以在这里留言。', time: '活动提醒' }
  ]
}
