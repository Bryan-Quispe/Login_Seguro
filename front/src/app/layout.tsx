import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
});

export const metadata: Metadata = {
  title: "Login Seguro - Autenticación Biométrica",
  description: "Sistema de autenticación seguro con verificación biométrica facial y protección anti-spoofing",
  keywords: ["login seguro", "autenticación biométrica", "reconocimiento facial", "seguridad"],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="es" className="dark">
      <body className={`${inter.variable} font-sans antialiased`}>
        <div className="min-h-screen bg-gradient-animated pattern-dots">
          {children}
        </div>
      </body>
    </html>
  );
}
