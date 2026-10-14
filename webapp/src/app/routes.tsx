import { IonReactRouter } from "@ionic/react-router";
import { Route, Routes } from "react-router-dom";

import { LoginPage } from "../features/auth/LoginPage";
import { ProfilePage } from "../features/accounts/ProfilePage";
import { RegisterPage } from "../features/accounts/RegisterPage";
import { RequireSession } from "../features/auth/RequireSession";
import { MovementsPage } from "../features/movements/MovementsPage";
import { TransferPage } from "../features/transfers/TransferPage";
import { RechargePage } from "../features/wallet/RechargePage";
import { AppShell } from "./AppShell";
import { HomePage } from "./HomePage";

/** Área privada: guardián de sesión + menú. Todo lo que no es /login pasa por aquí. */
function PrivateArea() {
  return (
    <RequireSession>
      <AppShell>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/recargar" element={<RechargePage />} />
          <Route path="/transferir" element={<TransferPage />} />
          <Route path="/movimientos" element={<MovementsPage />} />
          <Route path="/perfil" element={<ProfilePage />} />
        </Routes>
      </AppShell>
    </RequireSession>
  );
}

/** Rutas de la webapp (ADR-0007: Ionic + react-router-dom 6). /login y /registro son públicas y sin menú. */
export function AppRoutes() {
  return (
    <IonReactRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/registro" element={<RegisterPage />} />
        <Route path="/*" element={<PrivateArea />} />
      </Routes>
    </IonReactRouter>
  );
}
