import { IonButton } from "@ionic/react";

interface Props {
  page: number;
  lastPage: number;
  onPageChange: (page: number) => void;
}

/** Avanzar y retroceder entre páginas de 20 (HU-09 CA-6); operable por teclado (RNF-03.6). */
export function Pagination({ page, lastPage, onPageChange }: Props) {
  return (
    <nav
      aria-label="Paginación"
      style={{ display: "flex", alignItems: "center", gap: 12, marginTop: 16 }}
    >
      <IonButton
        fill="outline"
        disabled={page <= 1}
        onClick={() => {
          onPageChange(page - 1);
        }}
      >
        Anterior
      </IonButton>
      <span aria-live="polite" className="tai-muted">
        Página {page} de {lastPage}
      </span>
      <IonButton
        fill="outline"
        disabled={page >= lastPage}
        onClick={() => {
          onPageChange(page + 1);
        }}
      >
        Siguiente
      </IonButton>
    </nav>
  );
}
