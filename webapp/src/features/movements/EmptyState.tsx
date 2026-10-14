import { IonButton, IonIcon } from "@ionic/react";
import { walletOutline } from "ionicons/icons";

/** HU-09 CA-7: sin movimientos no hay tabla vacía, hay una explicación y el siguiente paso. */
export function EmptyState() {
  return (
    <div role="status" className="tai-card" style={{ textAlign: "center", padding: 32 }}>
      <IonIcon icon={walletOutline} aria-hidden="true" style={{ fontSize: 40 }} />
      <p style={{ fontWeight: 600, margin: "12px 0 4px" }}>Aún no tienes movimientos</p>
      <p className="tai-muted" style={{ margin: "0 0 16px" }}>
        Cuando recargues saldo o hagas una transferencia, aparecerá aquí.
      </p>
      <IonButton routerLink="/recargar">Recargar saldo</IonButton>
    </div>
  );
}
