"use client";

import { useEffect, useRef } from "react";
import { useTranslations } from "next-intl";
import { Loader2, Trash2, X } from "lucide-react";
import CompanyLogo from "./CompanyLogo";
import styles from "./ConfirmDeleteDialog.module.css";

export type DeleteSubject = { company: string; symbol?: string | null; detail?: string };
type Props = {
  subject: DeleteSubject | null; kind: "report" | "analysis"; pending: boolean; error?: string;
  onCancel: () => void; onConfirm: () => void;
};

export default function ConfirmDeleteDialog({ subject, kind, pending, error, onCancel, onConfirm }: Props) {
  const t = useTranslations("DeleteDialog");
  const dialog = useRef<HTMLDialogElement>(null);
  const cancel = useRef<HTMLButtonElement>(null);
  useEffect(() => {
    const element = dialog.current;
    if (!subject || !element) return;
    const previous = document.activeElement;
    const overflow = document.body.style.overflow;
    element.showModal();
    document.body.style.overflow = "hidden";
    cancel.current?.focus();
    return () => {
      element.close();
      document.body.style.overflow = overflow;
      if (previous instanceof HTMLElement && previous.isConnected) previous.focus();
    };
  }, [subject]);

  if (!subject) return null;
  return <dialog ref={dialog} className={styles.dialog} aria-labelledby="delete-dialog-title" aria-describedby="delete-dialog-description" aria-busy={pending} onCancel={event => { event.preventDefault(); if (!pending) onCancel(); }} onKeyDown={event => {
    if (event.key !== "Tab") return;
    const buttons = event.currentTarget.querySelectorAll<HTMLButtonElement>("button:not(:disabled)");
    const first = buttons[0], last = buttons[buttons.length - 1];
    if (!first) { event.preventDefault(); return; }
    if (document.activeElement === (event.shiftKey ? first : last)) {
      event.preventDefault(); (event.shiftKey ? last : first).focus();
    }
  }}>
    <div className={styles.content}>
      <div className={styles.top}><span className={styles.icon}><Trash2 size={22} aria-hidden="true" /></span><button type="button" onClick={onCancel} disabled={pending} className={styles.close} aria-label={t("close")}><X size={20} /></button></div>
      <p className={styles.eyebrow}>{t(kind === "report" ? "privateReport" : "savedAnalysis")}</p>
      <h2 id="delete-dialog-title">{t("title")}</h2>
      <p id="delete-dialog-description" className={styles.description}>{t(kind === "report" ? "reportDescription" : "analysisDescription")}</p>
      <div className={styles.subject}><CompanyLogo symbol={subject.symbol} company={subject.company} /><div><strong>{subject.company}</strong>{subject.detail && <p>{subject.detail}</p>}</div></div>
      {error && <p role="alert" className={styles.error}>{error}</p>}
      <div className={styles.actions}><button ref={cancel} type="button" onClick={onCancel} disabled={pending} className={styles.cancel}>{t("cancel")}</button><button type="button" onClick={onConfirm} disabled={pending} className={styles.confirm}>{pending ? <Loader2 size={17} className={styles.spinner} /> : <Trash2 size={17} />}{t(pending ? "deleting" : "confirm")}</button></div>
    </div>
  </dialog>;
}
