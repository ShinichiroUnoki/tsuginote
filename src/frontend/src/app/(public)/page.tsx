/**
 * ランディングページ — TsugiNoteの価値提案を訴求
 * ヒーロー・課題提示・機能紹介・料金・CTAの構成
 */
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { HeroSection } from "@/components/lp/HeroSection";
import { ProblemSection } from "@/components/lp/ProblemSection";
import { FeatureSection } from "@/components/lp/FeatureSection";
import { PricingSection } from "@/components/lp/PricingSection";
import { CtaSection } from "@/components/lp/CtaSection";

export default function LandingPage() {
  return (
    <div className="flex flex-col">
      <HeroSection />
      <ProblemSection />
      <FeatureSection />
      <PricingSection />
      <CtaSection />
    </div>
  );
}
