import { IonInput, IonSelect, IonSelectOption } from "@ionic/react";

import type { MovementType, MovementsFilterValues } from "./filters";
import { TYPE_OPTIONS } from "./labels";

interface Props {
  values: MovementsFilterValues;
  /** Mensaje de rango inválido, mostrado junto a "Desde" (HU-10 CA-2). */
  rangeError: string | null;
  /** Cada cambio vuelve a la primera página (CA-6): lo decide quien recibe el cambio. */
  onChange: (next: MovementsFilterValues) => void;
}

/**
 * Filtros del historial (HU-10): fechas con `input type="date"` nativo (valor AAAA-MM-DD, el
 * mismo formato de la API, operable por teclado) y selector de tipo. Se eligió sobre
 * `IonDatetime` por simplicidad y accesibilidad (research §5).
 */
export function MovementsFilters({ values, rangeError, onChange }: Props) {
  return (
    <form
      role="search"
      aria-label="Filtros del historial"
      className="tai-card"
      style={{
        display: "flex",
        flexWrap: "wrap",
        gap: 12,
        marginTop: 16,
        alignItems: "flex-start",
      }}
      onSubmit={(event) => {
        event.preventDefault();
      }}
    >
      <IonInput
        label="Desde"
        labelPlacement="stacked"
        type="date"
        fill="outline"
        value={values.from}
        errorText={rangeError ?? undefined}
        className={rangeError ? "ion-invalid ion-touched" : ""}
        style={{ flex: "1 1 180px" }}
        onIonInput={(event) => {
          onChange({ ...values, from: event.detail.value ?? "" });
        }}
      />
      <IonInput
        label="Hasta"
        labelPlacement="stacked"
        type="date"
        fill="outline"
        value={values.to}
        style={{ flex: "1 1 180px" }}
        onIonInput={(event) => {
          onChange({ ...values, to: event.detail.value ?? "" });
        }}
      />
      <IonSelect
        label="Tipo"
        labelPlacement="stacked"
        fill="outline"
        interface="alert"
        okText="Aceptar"
        cancelText="Cancelar"
        value={values.type}
        style={{ flex: "1 1 220px" }}
        onIonChange={(event) => {
          onChange({ ...values, type: event.detail.value as MovementType });
        }}
      >
        {TYPE_OPTIONS.map((option) => (
          <IonSelectOption key={option.value} value={option.value}>
            {option.label}
          </IonSelectOption>
        ))}
      </IonSelect>
    </form>
  );
}
