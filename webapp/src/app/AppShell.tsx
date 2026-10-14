import {
  IonContent,
  IonButton,
  IonHeader,
  IonIcon,
  IonItem,
  IonLabel,
  IonList,
  IonMenu,
  IonMenuToggle,
  IonRouterOutlet,
  IonSplitPane,
  IonTitle,
  IonToolbar,
} from "@ionic/react";
import {
  homeOutline,
  listOutline,
  logOutOutline,
  personOutline,
  swapHorizontalOutline,
  walletOutline,
} from "ionicons/icons";
import { useEffect, type ReactNode } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { useLocation, useNavigate } from "react-router-dom";

import { useLogout } from "../features/auth/useLogout";
import { setSessionExpiredHandler } from "../shared/api/client";

const NAV = [
  { href: "/", label: "Inicio", icon: homeOutline },
  { href: "/transferir", label: "Transferir", icon: swapHorizontalOutline },
  { href: "/recargar", label: "Recargar", icon: walletOutline },
  { href: "/movimientos", label: "Movimientos", icon: listOutline },
  { href: "/perfil", label: "Perfil", icon: personOutline },
];

/** Barra lateral del diseño: menú fijo en escritorio y deslizable en móvil (IonSplitPane). */
export function AppShell({ children }: { children: ReactNode }) {
  const { pathname } = useLocation();
  const navigate = useNavigate();
  const client = useQueryClient();
  const close = useLogout(() => {
    navigate("/login", { replace: true });
  });
  useEffect(() => {
    setSessionExpiredHandler(() => {
      void client.cancelQueries();
      client.clear();
      navigate("/login", { replace: true });
    });
    // BFCache puede restaurar documentos sin remontar React: revalidar al restaurar.
    const restore = (event: PageTransitionEvent) => {
      if (event.persisted) window.location.reload();
    };
    window.addEventListener("pageshow", restore);
    return () => {
      window.removeEventListener("pageshow", restore);
      setSessionExpiredHandler(() => {
        window.location.assign("/login");
      });
    };
  }, [client, navigate]);
  if (pathname === "/login" || pathname === "/registro") {
    return <IonRouterOutlet id="main">{children}</IonRouterOutlet>;
  }
  return (
    <IonSplitPane contentId="main" when="(min-width: 992px)">
      <IonMenu contentId="main" type="overlay">
        <IonHeader>
          <IonToolbar>
            <IonTitle className="tai-brand">TAI</IonTitle>
          </IonToolbar>
        </IonHeader>
        <IonContent>
          <IonList lines="none">
            {NAV.map((item) => (
              <IonMenuToggle key={item.href} autoHide={false}>
                <IonItem
                  routerLink={item.href}
                  routerDirection="none"
                  detail={false}
                  color={pathname === item.href ? "light" : undefined}
                  aria-current={pathname === item.href ? "page" : undefined}
                >
                  <IonIcon slot="start" icon={item.icon} aria-hidden="true" />
                  <IonLabel>{item.label}</IonLabel>
                </IonItem>
              </IonMenuToggle>
            ))}
            <IonItem
              button
              detail={false}
              disabled={close.pending}
              onClick={() => {
                void close.submit();
              }}
              aria-label="Cerrar sesión"
            >
              <IonIcon slot="start" icon={logOutOutline} aria-hidden="true" />
              <IonLabel>{close.pending ? "Cerrando sesión…" : "Cerrar sesión"}</IonLabel>
            </IonItem>
          </IonList>
          {close.error && (
            <div className="ion-padding">
              <p role="alert">{close.error}</p>
              <IonButton
                disabled={close.pending}
                onClick={() => {
                  void close.submit();
                }}
              >
                Reintentar cierre
              </IonButton>
            </div>
          )}
        </IonContent>
      </IonMenu>
      <IonRouterOutlet id="main">{children}</IonRouterOutlet>
    </IonSplitPane>
  );
}
