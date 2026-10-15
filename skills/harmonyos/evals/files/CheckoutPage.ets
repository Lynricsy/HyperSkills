// entry/src/main/ets/pages/CheckoutPage.ets
// Bug report: tapping "Apply SAVE10 and pay" charges the pre-coupon amount,
// although the Total text on screen shows the discounted amount right after.

class PaymentService {
  static charge(amountCents: number): void {
    console.info(`charging ${amountCents}`)
  }
}

@ObservedV2
class CartLine {
  @Trace priceCents: number = 0
  @Trace qty: number = 1

  constructor(priceCents: number, qty: number) {
    this.priceCents = priceCents
    this.qty = qty
  }
}

@Entry
@ComponentV2
struct CheckoutPage {
  @Local lines: CartLine[] = [new CartLine(1999, 1), new CartLine(450, 2)]
  @Local couponPercent: number = 0

  @Computed
  get totalCents(): number {
    const sum = this.lines.reduce((acc: number, l: CartLine) => acc + l.priceCents * l.qty, 0)
    return Math.round(sum * (100 - this.couponPercent) / 100)
  }

  build() {
    Column({ space: 12 }) {
      Text(`Total: ${(this.totalCents / 100).toFixed(2)}`)
      Button('Apply SAVE10 and pay')
        .onClick(() => {
          this.couponPercent = 10
          PaymentService.charge(this.totalCents)
        })
    }
    .padding(16)
  }
}
