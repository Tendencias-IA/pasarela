import {
  IonContent,
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
import type { ReactNode } from "react";
import { useLocation } from "react-router-dom";

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
            <IonMenuToggle autoHide={false}>
              <IonItem routerLink="/login" routerDirection="none" detail={false}>
                <IonIcon slot="start" icon={logOutOutline} aria-hidden="true" />
                <IonLabel>Cerrar sesión</IonLabel>
              </IonItem>
            </IonMenuToggle>
          </IonList>
        </IonContent>
      </IonMenu>
      <IonRouterOutlet id="main">{children}</IonRouterOutlet>
    </IonSplitPane>
  );
}
