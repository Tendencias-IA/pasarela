import { IonReactRouter } from "@ionic/react-router";
import { Route, Routes } from "react-router-dom";

import { LoginPage } from "../features/auth/LoginPage";
import { RegisterPage } from "../features/accounts/RegisterPage";
import { ProfilePage } from "../features/accounts/ProfilePage";
import { RechargePage } from "../features/wallet/RechargePage";
import { AppShell } from "./AppShell";
import { ComingSoonPage } from "./ComingSoonPage";
import { HomePage } from "./HomePage";

/** Rutas de la webapp (ADR-0007: Ionic + react-router-dom 6). */
export function AppRoutes() {
  return (
    <IonReactRouter>
      <AppShell>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/recargar" element={<RechargePage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/registro" element={<RegisterPage />} />
          <Route path="/transferir" element={<ComingSoonPage title="Transferir" story="HU-06" />} />
          <Route
            path="/movimientos"
            element={<ComingSoonPage title="Movimientos" story="HU-09" />}
          />
          <Route path="/perfil" element={<ProfilePage />} />
        </Routes>
      </AppShell>
    </IonReactRouter>
  );
}
