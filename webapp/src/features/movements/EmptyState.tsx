import { IonButton, IonIcon } from "@ionic/react";
import { searchOutline, walletOutline } from "ionicons/icons";

interface Props {
  /** Hay filtros activos: el vacío es "sin coincidencias", no "sin movimientos" (HU-10 CA-7). */
  filtered?: boolean;
  onClearFilters?: () => void;
}

/**
 * HU-09 CA-7: sin movimientos no hay tabla vacía, hay una explicación y el siguiente paso.
 * HU-10 CA-7: con filtros sin coincidencias se explica y se ofrece quitarlos; los valores
 * elegidos no se tocan hasta que el usuario lo pida.
 */
export function EmptyState({ filtered = false, onClearFilters }: Props) {
  if (filtered) {
    return (
      <div role="status" className="tai-card" style={{ textAlign: "center", padding: 32 }}>
        <IonIcon icon={searchOutline} aria-hidden="true" style={{ fontSize: 40 }} />
        <p style={{ fontWeight: 600, margin: "12px 0 4px" }}>No hay movimientos con esos filtros</p>
        <p className="tai-muted" style={{ margin: "0 0 16px" }}>
          Prueba con otro rango de fechas u otro tipo de movimiento.
        </p>
        <IonButton onClick={onClearFilters}>Quitar filtros</IonButton>
      </div>
    );
  }
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
