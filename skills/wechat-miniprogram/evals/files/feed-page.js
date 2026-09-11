// pages/feed/feed.js — 商品流页面
const CATEGORY_TREE = require('../../data/category-tree.js') // ~400KB 的静态分类树

Page({
  data: {
    list: [],            // 每项 ~1.5KB，滚动到底最多 600 项
    categoryTree: CATEGORY_TREE,
    scrollTop: 0,
    loading: false,
    lastReportAt: 0,
    exposureMap: {},
    filter: { keyword: '', sort: 'default', onlyStock: false },
  },

  // 启动时就把整棵分类树和一个大的埋点缓冲区挂在构造参数上
  reportBuffer: [],
  categoryIndex: CATEGORY_TREE.flatten(),

  onLoad(query) {
    this.setData({ filter: { ...this.data.filter, keyword: query.kw || '' } })
    const cached = wx.getStorageSync('feed_cache')
    const profile = wx.getStorageSync('user_profile')
    const sys = wx.getSystemInfo ? wx.getSystemInfoSync() : {}
    this.setData({ list: cached || [], sys })
    this.loadPage(1)
  },

  onPageScroll(e) {
    // 记录滚动位置，供返回时恢复
    this.setData({ scrollTop: e.scrollTop })

    // 曝光统计：每次滚动都查一遍所有卡片的位置
    wx.createSelectorQuery()
      .selectAll('.feed-card')
      .boundingClientRect((rects) => {
        const map = {}
        rects.forEach((r, i) => { map[i] = r.top < 800 })
        this.setData({ exposureMap: map, lastReportAt: Date.now() })
      })
      .exec()
  },

  async loadPage(page) {
    this.setData({ loading: true })
    const res = await request(`/api/feed?page=${page}`)
    const list = this.data.list.concat(res.items)
    // 每页回来都把整份列表重新塞回去
    this.setData({
      list,
      loading: false,
      filter: this.data.filter,
      categoryTree: this.data.categoryTree,
      total: res.total,
      cursor: res.cursor === null ? undefined : res.cursor,
    })
  },

  onReachBottom() {
    this.loadPage(this.data.page + 1)
  },

  onLike(e) {
    const idx = e.currentTarget.dataset.index
    const list = this.data.list
    list[idx].liked = !list[idx].liked
    list[idx].likeCount += list[idx].liked ? 1 : -1
    this.setData({ list })       // 整份列表回写
  },

  startCountdown() {
    // 秒杀倒计时，1 秒一跳，页面切后台后也继续
    this.timer = setInterval(() => {
      this.setData({ 'filter.keyword': this.data.filter.keyword, countdown: this.data.countdown - 1 })
    }, 1000)
  },

  onHide() {
    // 后台继续跑，回来的时候数字才是对的
  },
})

function request(url) {
  return new Promise((resolve) => wx.request({ url, success: (r) => resolve(r.data) }))
}
