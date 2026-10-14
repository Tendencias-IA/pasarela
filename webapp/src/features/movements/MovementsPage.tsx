import {
  IonButton,
  IonButtons,
  IonContent,
  IonHeader,
  IonList,
  IonMenuButton,
  IonPage,
  IonTitle,
  IonToolbar,
} from "@ionic/react";
import { useEffect, useRef } from "react";
import { useSearchParams } from "react-router-dom";

import { EmptyState } from "./EmptyState";
import { MovementItem } from "./MovementItem";
import { Pagination } from "./Pagination";
import { useMovements } from "./useMovements";

function pageFromParams(params: URLSearchParams): number {
  const raw = Number(params.get("page") ?? "1");
  return Number.isInteger(raw) && raw >= 1 ? raw : 1;
}

/** HU-09: historial paginado de la billetera del usuario autenticado. */
export function MovementsPage() {
  const [params, setParams] = useSearchParams();
  const page = pageFromParams(params);
  const { data, isPending, isError, refetch, lastPage, isOutOfRange } = useMovements(page);
  const contentRef = useRef<HTMLIonContentElement>(null);

  const goTo = (next: number) => {
    setParams(next === 1 ? {} : { page: String(next) });
    void contentRef.current?.scrollToTop(200);
  };

  // FR-009: una página más allá de la última no es un error; se lleva a la última válida.
  useEffect(() => {
    if (isOutOfRange)
      setParams(lastPage === 1 ? {} : { page: String(lastPage) }, { replace: true });
  }, [isOutOfRange, lastPage, setParams]);

  return (
    <IonPage>
      <IonHeader>
        <IonToolbar>
          <IonButtons slot="start">
            <IonMenuButton />
          </IonButtons>
          <IonTitle>Movimientos</IonTitle>
        </IonToolbar>
      </IonHeader>
      <IonContent ref={contentRef} className="ion-padding">
        <h1 className="tai-title">Movimientos</h1>
        <p className="tai-muted">
          Recargas y transferencias de tu billetera, de la más reciente a la más antigua.
        </p>
        {isPending && <p role="status">Cargando…</p>}
        {isError && (
          <div role="alert" className="tai-card" style={{ marginTop: 16 }}>
            <p style={{ margin: "0 0 12px" }}>No se pudo cargar el historial.</p>
            <IonButton
              fill="outline"
              onClick={() => {
                void refetch();
              }}
            >
              Reintentar
            </IonButton>
          </div>
        )}
        {data !== undefined && data.total === 0 && <EmptyState />}
        {data !== undefined && data.total > 0 && (
          <>
            <IonList
              role="list"
              aria-label="Movimientos"
              className="tai-card"
              style={{ marginTop: 16 }}
            >
              {data.items.map((movement) => (
                <MovementItem key={movement.id} movement={movement} />
              ))}
            </IonList>
            <Pagination page={data.page} lastPage={lastPage} onPageChange={goTo} />
          </>
        )}
      </IonContent>
    </IonPage>
  );
}
