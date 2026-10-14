import { IonBadge, IonItem, IonLabel } from "@ionic/react";

import { formatDateTime } from "../../shared/dates";
import { formatCOP } from "../../shared/money";
import type { MovementOut } from "./api";
import { counterpartyLabel, directionLabel, statusLabel } from "./labels";

/** Una fila del historial: tipo/dirección, contraparte, fecha, monto y estado (HU-09 CA-2). */
export function MovementItem({ movement }: { movement: MovementOut }) {
  const success = movement.status === "exitosa";
  const counterparty = counterpartyLabel(movement.direction, movement.counterparty);
  const title = counterparty
    ? `${directionLabel(movement.direction)} ${counterparty}`
    : directionLabel(movement.direction);
  return (
    <IonItem
      role="listitem"
      lines="full"
      data-status={movement.status}
      aria-label={`${title}, ${formatCOP(movement.amount)}, ${statusLabel(movement.status)}, ${formatDateTime(movement.created_at)}`}
    >
      <IonLabel>
        <h2 style={{ fontWeight: 600 }}>{title}</h2>
        <p className="tai-muted">{formatDateTime(movement.created_at)}</p>
      </IonLabel>
      <div slot="end" style={{ textAlign: "right" }}>
        <p className="tai-amount" style={{ margin: 0, fontWeight: 600 }}>
          {success && movement.direction === "enviada" ? "−" : ""}
          {formatCOP(movement.amount)}
        </p>
        <IonBadge color={success ? "success" : "danger"}>{statusLabel(movement.status)}</IonBadge>
      </div>
    </IonItem>
  );
}
