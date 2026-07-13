import React from "react";
import { Link } from "react-router-dom";

export default function Footer() {
  return (
    <footer
      data-testid="site-footer"
      className="border-t border-edge bg-cream mt-24"
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16 grid grid-cols-1 md:grid-cols-4 gap-12">
        <div className="md:col-span-2">
          <div className="font-serif text-3xl font-bold text-terracotta uppercase">
            Purnasree
          </div>
          <p className="tag text-muted2 mt-1">Books & Stationery</p>
          <p className="mt-6 max-w-md text-sm text-muted2 leading-relaxed">
            A family run shop supplying NCERT textbooks and everyday
            stationery to students, teachers and offices — for over two
            decades.
          </p>
        </div>
        <div>
          <p className="tag text-ink mb-4">Shop</p>
          <ul className="space-y-2 text-sm text-muted2">
            <li><Link to="/products?category=NCERT Books" className="hover:text-terracotta">NCERT Books</Link></li>
            <li><Link to="/products?category=Notebooks" className="hover:text-terracotta">Notebooks</Link></li>
            <li><Link to="/products?category=Pens & Pencils" className="hover:text-terracotta">Pens &amp; Pencils</Link></li>
            <li><Link to="/products?category=Art Supplies" className="hover:text-terracotta">Art Supplies</Link></li>
          </ul>
        </div>
        <div>
          <p className="tag text-ink mb-4">Store</p>
          <ul className="space-y-2 text-sm text-muted2">
            <li>Order via WhatsApp</li>
            <li>Cash on Delivery</li>
            <li>Same-day pickup</li>
            <li><Link to="/admin/login" data-testid="footer-admin-link" className="hover:text-terracotta">Owner Login</Link></li>
          </ul>
        </div>
      </div>
      <div className="border-t border-edge py-6 text-center text-xs text-muted2">
        © {new Date().getFullYear()} PURNASREE Books & Stationery · All rights reserved.
      </div>
    </footer>
  );
}
