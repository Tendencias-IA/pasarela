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
import {
  DEFAULT_FILTERS,
  hasActiveFilters,
  parseFilters,
  parsePage,
  rangeError,
  toSearchParams,
  type MovementsFilterValues,
} from "./filters";
import { MovementItem } from "./MovementItem";
import { MovementsFilters } from "./MovementsFilters";
import { Pagination } from "./Pagination";
import { useMovements } from "./useMovements";

/**
 * HU-09: historial paginado de la billetera del usuario autenticado.
 * HU-10: filtros de fecha y tipo; viven en la URL junto con la página (CA-7), así recargar y
 * "atrás" los conservan.
 */
export function MovementsPage() {
  const [params, setParams] = useSearchParams();
  const page = parsePage(params);
  const filters = parseFilters(params);
  const invalidRange = rangeError(filters);
  const { data, isLoading, isError, refetch, lastPage, isOutOfRange } = useMovements({
    page,
    ...filters,
  });
  const contentRef = useRef<HTMLIonContentElement>(null);

  const goTo = (next: number) => {
    setParams(toSearchParams(filters, next));
    void contentRef.current?.scrollToTop(200);
  };

  // HU-10 CA-6: cualquier cambio de filtro vuelve a la primera página.
  const changeFilters = (next: MovementsFilterValues) => {
    setParams(toSearchParams(next, 1));
  };

  // FR-009: una página más allá de la última no es un error; se lleva a la última válida.
  useEffect(() => {
    if (isOutOfRange) setParams(toSearchParams(parseFilters(params), lastPage), { replace: true });
  }, [isOutOfRange, lastPage, params, setParams]);

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
        <MovementsFilters values={filters} rangeError={invalidRange} onChange={changeFilters} />
        {isLoading && <p role="status">Cargando…</p>}
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
        {data !== undefined && data.total === 0 && (
          <EmptyState
            filtered={hasActiveFilters(filters)}
            onClearFilters={() => {
              changeFilters(DEFAULT_FILTERS);
            }}
          />
        )}
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
