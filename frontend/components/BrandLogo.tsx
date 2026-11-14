import Image from "next/image";

export default function BrandLogo({ size = 36 }: { size?: number }) {
  return <Image src="/brand/finanalyzer.jpg" width={size} height={size} alt="" style={{ width: size, height: size, borderRadius: "50%", flexShrink: 0 }} />;
}
