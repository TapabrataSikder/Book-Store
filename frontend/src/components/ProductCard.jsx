import React from "react";
import { Link } from "react-router-dom";
import { Plus } from "lucide-react";
import { useCart } from "../context/CartContext";
import { formatINR } from "../lib/api";

export default function ProductCard({ product }) {
  const { addItem } = useCart();

  return (
    <div
      data-testid={`product-card-${product.id}`}
      className="group relative flex flex-col bg-white border border-edge hover:border-terracotta transition-colors"
    >
      <Link to={`/product/${product.id}`} className="block">
        <div className="relative aspect-[4/5] overflow-hidden border-b border-edge bg-cream">
          {product.image_url ? (
            <img
              src={product.image_url}
              alt={product.name}
              className="w-full h-full object-cover group-hover:scale-[1.03] transition-transform duration-500"
              loading="lazy"
            />
          ) : (
            <div className="w-full h-full flex items-center justify-center text-muted2 text-xs">
              No image
            </div>
          )}
          {product.featured && (
            <span className="absolute top-3 left-3 bg-ink text-paper tag px-2 py-1">
              Bestseller
            </span>
          )}
        </div>
      </Link>
      <div className="p-4 sm:p-5 flex flex-col flex-grow">
        <p className="tag text-muted2 mb-2">{product.category}</p>
        <Link to={`/product/${product.id}`}>
          <h3 className="editorial-heading text-lg sm:text-xl line-clamp-2 mb-3 text-ink hover:text-terracotta transition-colors">
            {product.name}
          </h3>
        </Link>
        <div className="mt-auto flex items-center justify-between gap-3 pt-3">
          <span className="font-serif text-2xl font-semibold text-terracotta">
            {formatINR(product.price)}
          </span>
          <button
            data-testid={`add-to-cart-${product.id}`}
            onClick={(e) => {
              e.preventDefault();
              addItem(product, 1);
            }}
            className="border border-ink bg-transparent text-ink hover:bg-ink hover:text-paper py-2 px-3 transition-colors tag flex items-center gap-1"
          >
            <Plus className="w-3.5 h-3.5" /> Add
          </button>
        </div>
      </div>
    </div>
  );
}
