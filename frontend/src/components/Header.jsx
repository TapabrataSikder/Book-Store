import React from "react";
import { Link, useNavigate } from "react-router-dom";
import { ShoppingBag, Search } from "lucide-react";
import { useCart } from "../context/CartContext";

function Header() {
  const navigate = useNavigate();
  const { count, setDrawerOpen } = useCart();

  return (
    <header
      data-testid="site-header"
      className="bg-paper sticky top-0 z-40 border-b border-edge"
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-20">
          <Link
            to="/"
            data-testid="logo-link"
            className="flex flex-col leading-none"
          >
            <span className="font-serif text-2xl sm:text-3xl font-bold tracking-tight text-terracotta uppercase">
              Purnasree
            </span>
            <span className="tag text-muted2 mt-0.5 hidden sm:block">
              Books &amp; Stationery · Est. 1998
            </span>
          </Link>

          <nav className="hidden md:flex items-center gap-10">
            <Link
              to="/"
              data-testid="nav-home"
              className="tag text-ink hover:text-terracotta transition-colors"
            >
              Home
            </Link>
            <Link
              to="/products"
              data-testid="nav-products"
              className="tag text-ink hover:text-terracotta transition-colors"
            >
              Shop All
            </Link>
            <Link
              to="/products?category=NCERT Books"
              data-testid="nav-ncert"
              className="tag text-ink hover:text-terracotta transition-colors"
            >
              NCERT Books
            </Link>
          </nav>

          <div className="flex items-center gap-2">
            <button
              onClick={() => navigate("/products")}
              data-testid="header-search-btn"
              className="p-2 hover:bg-cream transition-colors"
              aria-label="Search"
            >
              <Search className="w-5 h-5 text-ink" />
            </button>
            <button
              onClick={() => setDrawerOpen(true)}
              data-testid="header-cart-btn"
              className="p-2 hover:bg-cream transition-colors relative"
              aria-label="Cart"
            >
              <ShoppingBag className="w-5 h-5 text-ink" />
              {count > 0 && (
                <span
                  data-testid="cart-badge"
                  className="absolute -top-0.5 -right-0.5 bg-terracotta text-white text-[10px] font-bold w-5 h-5 flex items-center justify-center"
                >
                  {count}
                </span>
              )}
            </button>
          </div>
        </div>
      </div>
    </header>
  );
}

export default Header;
