import { Github, Instagram, Linkedin } from "lucide-react";
import styles from "./SiteCredit.module.css";

const profiles = [
  { name: "LinkedIn", href: "https://www.linkedin.com/in/andr%C3%A9-vitale-388a42272", Icon: Linkedin },
  { name: "Instagram", href: "https://www.instagram.com/andrevitale/", Icon: Instagram },
  { name: "GitHub", href: "https://github.com/andrevitale1-cyber", Icon: Github },
];

export default function SiteCredit({ locale }: { locale: string }) {
  const en = locale === "en";
  return <div className={styles.credit}>
    <p>site crafted by <span>André Vitale</span></p>
    <nav aria-label={en ? "André Vitale’s social profiles" : "Redes sociais de André Vitale"}>
      {profiles.map(({ name, href, Icon }) => <a key={name} href={href} target="_blank" rel="noopener noreferrer" title={name} aria-label={`André Vitale ${en ? "on" : "no"} ${name}`}><Icon size={18} aria-hidden="true" /></a>)}
    </nav>
  </div>;
}
