// entry/src/main/ets/pages/CartPage.ets
// The quantity stepper does not refresh the total, and the "clear" button in
// the toolbar sometimes updates the badge and sometimes does not.
// Project compatibleSdkVersion is 6.0.0(20).

import { UIUtils } from '@kit.ArkUI'

@ObservedV2
class LineItem {
  @Trace qty: number = 1
  sku: string = ''
  price: number = 0

  constructor(sku: string, price: number) {
    this.sku = sku
    this.price = price
  }
}

@Observed
class Cart {
  lines: LineItem[] = []
  coupon: string = ''
}

@ComponentV2
struct QtyStepper {
  @Prop line: LineItem
  @Param @Once label: string = 'qty'
  @Link total: number

  build() {
    Row() {
      Button('-').onClick(() => { this.line.qty-- })
      Text(`${this.label} ${this.line.qty}`)
      Button('+').onClick(() => { this.line.qty++ })
    }
  }
}

@Component
struct CartToolbar {
  @Param cart: Cart
  @Local badge: number = 0

  @Monitor('cart.lines')
  onLines() {
    this.badge = this.cart.lines.length
  }

  build() {
    Row() {
      Text(`${this.badge}`)
      Button('clear').onClick(() => { this.cart.lines = [] })
    }
  }
}

@Entry
@Component
struct CartPage {
  @State cart: Cart = new Cart()
  @State total: number = 0
  @Provide('theme') theme: string = 'light'
  @Consumer('theme') inherited: string = 'light'

  aboutToAppear() {
    this.cart.lines.push(new LineItem('sku-1', 1200))
    this.cart.lines.push(new LineItem('sku-2', 800))
    this.recompute()
  }

  recompute() {
    let sum = 0
    this.cart.lines.forEach((l: LineItem) => { sum += l.qty * l.price })
    this.total = sum
  }

  build() {
    Column() {
      CartToolbar({ cart: this.cart })
      ForEach(this.cart.lines, (l: LineItem) => {
        QtyStepper({ line: l, label: 'qty', total: this.total })
      })
      Text(`total ${this.total}`)
    }
  }
}
