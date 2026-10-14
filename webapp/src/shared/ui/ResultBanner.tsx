import { IonIcon } from "@ionic/react";
import { checkmarkCircle, closeCircle } from "ionicons/icons";
import type { ReactNode } from "react";

interface Props {
  kind: "success" | "rejected";
  title: string;
  children?: ReactNode;
}

/** Resultado de una operación: texto e icono, nunca solo color (RNF-03.4). */
export function ResultBanner({ kind, title, children }: Props) {
  const success = kind === "success";
  return (
    <div
      role={success ? "status" : "alert"}
      data-result={kind}
      style={{
        display: "flex",
        gap: 12,
        alignItems: "flex-start",
        padding: 14,
        borderRadius: 10,
        background: success ? "var(--tai-teal-tint)" : "var(--tai-coral-tint)",
        color: success ? "var(--ion-color-success)" : "var(--ion-color-danger)",
      }}
    >
      <IonIcon
        icon={success ? checkmarkCircle : closeCircle}
        aria-hidden="true"
        style={{ fontSize: 22 }}
      />
      <div>
        <p style={{ margin: 0, fontWeight: 600 }}>{title}</p>
        {children}
      </div>
    </div>
  );
}
