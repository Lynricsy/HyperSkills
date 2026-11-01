import 'package:meta/meta.dart';

@immutable
class CartLine {
  const CartLine({required this.unitPriceCents, required this.quantity});

  final int unitPriceCents;
  final int quantity;
}

/// Sums the cart in integer cents and applies a percentage discount.
///
/// Fixed today: the discount used to be applied to each line and rounded per
/// line, which lost up to one cent per line. It is now applied once to the
/// subtotal and rounded half-up.
int cartTotalCents(List<CartLine> lines, {int discountPercent = 0}) {
  if (discountPercent < 0 || discountPercent > 100) {
    throw RangeError.range(discountPercent, 0, 100, 'discountPercent');
  }
  final subtotal = lines.fold<int>(
    0,
    (sum, line) => sum + line.unitPriceCents * line.quantity,
  );
  final discount = (subtotal * discountPercent + 50) ~/ 100;
  return subtotal - discount;
}
