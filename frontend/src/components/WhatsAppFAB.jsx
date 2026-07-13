import React, { useEffect, useState } from "react";
import { MessageCircle } from "lucide-react";
import { api } from "../lib/api";

export default function WhatsAppFAB() {
  const [phone, setPhone] = useState("");

  useEffect(() => {
    api.get("/store-info").then((r) => setPhone(r.data.whatsapp || "")).catch(() => {});
  }, []);

  if (!phone) return null;
  const msg = encodeURIComponent(
    "Hello PURNASREE! I would like to enquire about your books and stationery.",
  );
  const href = `https://wa.me/${phone}?text=${msg}`;

  return (
    <a
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      data-testid="whatsapp-fab"
      className="fixed bottom-6 right-6 md:bottom-8 md:right-8 bg-whatsapp text-white px-5 py-3.5 rounded-full shadow-lg hover:-translate-y-1 transition-transform z-40 flex items-center gap-2 font-semibold"
      aria-label="Chat on WhatsApp"
    >
      <MessageCircle className="w-5 h-5" />
      <span className="hidden sm:inline text-sm tracking-wide">WhatsApp</span>
    </a>
  );
}
