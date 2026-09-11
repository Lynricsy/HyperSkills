// app/components/ProductGrid.tsx
"use client";

import { useEffect, useState } from "react";

type Product = { id: string; title: string; price: number; hero: string };
type Review = { productId: string; score: number };

export function ProductGrid({ category }: { category: string }) {
  const [products, setProducts] = useState<Product[]>([]);
  const [reviews, setReviews] = useState<Review[]>([]);
  const [banner, setBanner] = useState<{ image: string; copy: string } | null>(null);

  useEffect(() => {
    (async () => {
      const p = await fetch(`/api/products?category=${category}`).then((r) => r.json());
      setProducts(p);
      const r = await fetch(`/api/reviews?category=${category}`).then((r) => r.json());
      setReviews(r);
      const b = await fetch(`/api/banner?category=${category}`).then((r) => r.json());
      setBanner(b);
    })();
  }, [category]);

  return (
    <section>
      {banner && <img src={banner.image} alt={banner.copy} />}
      <div className="grid">
        {products.map((product) => (
          <article key={product.id}>
            <img src={product.hero} alt={product.title} />
            <h3>{product.title}</h3>
            <p>${product.price.toFixed(2)}</p>
            <span>
              {reviews.filter((rev) => rev.productId === product.id).length} reviews
            </span>
          </article>
        ))}
      </div>
    </section>
  );
}
