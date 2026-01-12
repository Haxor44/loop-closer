import Hero from "@/components/Hero";
import Pricing from "@/components/Pricing";
import Features from "@/components/Features";
import Waitlist from "@/components/Waitlist";
import Footer from "@/components/Footer";

export default function Home() {
  return (
    <main className="min-h-screen">
      <Hero />
      <Features />
      <Pricing />
      <Waitlist />
      <Footer />
    </main>
  );
}
