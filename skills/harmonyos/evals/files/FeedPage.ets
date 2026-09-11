// entry/src/main/ets/pages/FeedPage.ets
// Ported straight over from our React Native / TypeScript codebase.
// DevEco says "多个编译错误" but we cannot tell which lines are the real problem.

import { router } from '@kit.ArkUI'
import promptAction from '@ohos.promptAction'

type FeedItemLike = {
  id: number
  title: string
  tags: string[]
}

interface Renderable {
  render(): string
}

// We reuse the same shape everywhere, so structural compatibility is convenient.
class FeedItem {
  id: number = 0
  title: string = ''
  tags: string[] = []
  render(): string {
    return this.title
  }
}

class Banner {
  id: number = 0
  title: string = ''
  tags: string[] = []
  render(): string {
    return '[banner] ' + this.title
  }
}

var CACHE_KEY = 'feed-cache'

function parseFeed(raw: any): FeedItemLike[] {
  const payload = JSON.parse(raw) as any
  const out: FeedItemLike[] = []
  for (const key in payload.items) {
    const { id, title, tags } = payload.items[key]
    out.push({ id: id, title: title, tags: tags })
  }
  return out
}

const SORTS = ['hot', 'new', 'top'] as const

function decorate(item: FeedItemLike) {
  // tag the object so the list renderer can branch on it later
  ;(item as any).__decorated = true
  delete (item as any).tags
  return item
}

function load(handler) {
  function retry(n: number) {
    if (n <= 0) {
      throw 'giving up on feed'
    }
    setTimeout(function () {
      retry(n - 1)
    }, 200)
  }
  retry(3)
  handler(globalThis.lastFeed)
}

@Entry
@Component
struct FeedPage {
  @State items: FeedItemLike[] = []
  @State sort: string = SORTS[0]
  @State selected?: FeedItemLike

  aboutToAppear() {
    load(this.onLoaded.bind(this))
  }

  onLoaded(raw: string) {
    this.items = parseFeed(raw).map(decorate)
    const renderables: Renderable[] = this.items as Renderable[]
    promptAction.showToast({ message: `loaded ${renderables.length}` })
  }

  openDetail(item: FeedItemLike) {
    router.pushUrl({ url: 'pages/DetailPage', params: { item: item, onDone: () => this.reload() } })
  }

  reload() {
    this.items = [...this.items]
  }

  build() {
    Column() {
      ForEach(this.items, (item: FeedItemLike) => {
        Row() {
          Text(item.title)
          if ('tags' in item) {
            Text(item.tags.join(','))
          }
        }
        .onClick(() => this.openDetail(item))
      })
    }
  }
}
