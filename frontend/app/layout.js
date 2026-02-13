import "./globals.css";

export const metadata = {
  title: "Legal RAG",
  description: "Legal RAG chat",
};

export default function RootLayout({ children }) {
  return (
    <html lang="ru">
      <body>{children}</body>
    </html>
  );
}
