using System;

namespace Billing
{
    /// <summary>Applies a percentage discount to an amount in cents.</summary>
    public sealed class DiscountPolicy
    {
        private readonly int _percent;

        /// <exception cref="ArgumentOutOfRangeException">percent is below 0 or above 100.</exception>
        public DiscountPolicy(int percent)
        {
            if (percent < 0 || percent > 100)
            {
                throw new ArgumentOutOfRangeException(nameof(percent), percent, "Discount must be between 0 and 100.");
            }
            _percent = percent;
        }

        /// <summary>Discounted amount, rounding the discount down to whole cents.</summary>
        public long Apply(long amountCents)
        {
            return amountCents - (amountCents * _percent / 100);
        }
    }
}
