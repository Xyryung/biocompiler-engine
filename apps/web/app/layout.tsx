import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "BioCompiler · Experiment workspace",
  description: "Simulation-only PET assay planning, compilation, and observation.",
};

export default function Layout({ children }: { children: React.ReactNode }) {
  return <html lang="en"><body>{children}</body></html>;
}
