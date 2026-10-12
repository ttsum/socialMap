Component({ properties: { activity: { type: Object, value: null } }, methods: { open() { this.triggerEvent('open', { id: this.data.activity.id }) } } })
