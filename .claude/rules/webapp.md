---
paths:
  - "webapp/**"
---

# Webapp (`webapp/`): React 18 + Vite + TypeScript

Aplica a todo archivo bajo `webapp/`. Cubre RNF-03 (usabilidad y accesibilidad) y la
parte de cliente de RNF-01 y RNF-06.

## Herramientas obligatorias

| Herramienta | Configuración | Falla el CI si |
| --- | --- | --- |
| TypeScript | `strict: true`, `noUncheckedIndexedAccess: true` | cualquier error de `tsc --noEmit` |
| ESLint + Prettier | `eslint-config` con `react-hooks`, `jsx-a11y`, `@typescript-eslint` | cualquier hallazgo |
| Vitest + Testing Library | cobertura de `src/features/**` y `src/shared/**` | un test rojo |
| Playwright | `e2e/`, proyectos `desktop-chromium` y `mobile-chromium` | un escenario rojo |

```bash
cd webapp && npm run lint && npm run typecheck && npm run test && npm run e2e
```

## Estructura

```text
webapp/
├── src/
│   ├── app/                 # router, providers, layout, temporizador de inactividad
│   ├── features/            # espejo de los módulos de la API
│   │   ├── accounts/        # RegisterPage, ProfilePage, hooks, api.ts, __tests__/
│   │   ├── auth/            # LoginPage, useSession, api.ts
│   │   ├── wallet/          # BalanceCard, RechargePage
│   │   ├── transfers/       # TransferForm, TransferConfirm, TransferResult
│   │   └── movements/       # MovementsPage, MovementsFilters, MovementRow
│   ├── shared/
│   │   ├── api/             # client.ts (fetch + cookies + X-Requested-With), types.gen.ts, problem.ts
│   │   ├── ui/              # envoltorios finos sobre Ionic: MoneyInput, ResultBanner, EmptyState
│   │   ├── money/           # formatCOP, parseAmountInput
│   │   └── i18n/            # mensajes en español por `code` de error
│   └── theme/
│       └── variables.css    # variables de tema de Ionic
├── e2e/
│   ├── pages/               # page objects
│   ├── fixtures/            # usuarios y montos ficticios
│   └── *.spec.ts            # un archivo por historia: hu-06-preparar-transferencia.spec.ts
└── playwright.config.ts
```

- Una feature no importa componentes de otra feature; lo compartido va a `shared/`.
  Razón: igual que en la API, una HU se implementa en una carpeta.
- Los tipos de la API se generan con `npm run api:types` desde `api/openapi.yaml` a
  `src/shared/api/types.gen.ts`; ese archivo no se edita a mano.

## Componentes y estado

- Librería de componentes: **Ionic React** (ADR-0007). Toda pantalla es un `IonPage` con
  `IonHeader`/`IonToolbar`/`IonTitle` y `IonContent`; formularios con `IonInput`,
  `IonButton`, `IonList`/`IonItem`; resultados con `IonAlert` o `IonToast`; listas largas
  con `IonInfiniteScroll`. No se mezclan otras librerías de UI ni frameworks CSS.
  `shared/ui/` solo contiene envoltorios que añaden convenciones del proyecto sobre un
  componente de Ionic (por ejemplo, `MoneyInput` fija `inputmode="decimal"` y el formato
  COP). Razón: RNF-03 pide responsive y accesibilidad consistentes; Ionic las trae de
  serie y evita reconstruirlas en cada historia.
- Navegación con `@ionic/react-router` y `react-router-dom` 6 (`IonReactRouter`,
  `IonRouterOutlet`, `Route`, `useNavigate`). Ionic 9 no soporta react-router 7.
- Componentes de función con hooks. Sin clases, sin `any`, sin `// @ts-ignore`.
- Estado del servidor (saldo, movimientos, perfil) con TanStack Query; estado de
  formulario con React Hook Form; estado global de UI mínimo (sesión activa) en un
  contexto en `app/`. No se añade Redux ni similar.
- Después de una transferencia o recarga exitosa se invalida la query de saldo y la de
  movimientos; la pantalla de resultado muestra el `balance_after` de la respuesta sin
  esperar la recarga (HU-05 CA-3).
- Un componente que no se puede nombrar sin "y" se divide (`TransferFormAndSummary` →
  `TransferForm` + `TransferSummary`).

## Formularios y validación

- Validación de formato en el cliente para feedback inmediato (mismas reglas que la
  API: teléfono 10 dígitos, contraseña 8+ con letra y número, montos dentro de rango),
  pero la decisión siempre es del servidor: el formulario muestra los `errors[]` del
  `422` campo por campo (RNF-03.2).
- Campos obligatorios marcados visualmente y con `aria-required`. Cada error se asocia al
  campo con `aria-describedby`.
- Los montos se capturan como texto, se normalizan con `parseAmountInput` y se envían
  como cadena `"150000.00"`; nunca se hace aritmética con `Number` para decidir nada.

```tsx
// Correcto
<IonInput
  label="Monto (COP)"
  labelPlacement="stacked"
  inputmode="decimal"
  required
  errorText={errors.amount?.message}
  className={errors.amount ? "ion-invalid ion-touched" : ""}
  onIonInput={(e) => setValue("amount", String(e.detail.value ?? ""))}
/>
```

```tsx
// Incorrecto
<input placeholder="Monto" onChange={(e) => setAmount(parseFloat(e.target.value))} />
```

Diferencia: la segunda versión no tiene etiqueta accesible, pierde precisión con
`parseFloat` y no muestra errores asociados al campo. En Ionic la etiqueta se pasa por la
propiedad `label` (no con `<label for>`), porque el `input` real vive en el shadow DOM.

## Resultado de operaciones

- Toda operación termina en una pantalla o alerta de resultado que distingue
  visualmente y por texto `exitosa` de `rechazada` (RNF-03.4). Nunca solo color: icono
  más texto, `role="status"` para éxito y `role="alert"` para rechazo.
- Antes de confirmar una transferencia se muestra el resumen con `recipient.name_masked`,
  `recipient.phone_masked` y el monto formateado (HU-06 CA-7, RNF-03.3). El botón de
  confirmar se deshabilita tras el primer clic y reutiliza la misma `Idempotency-Key`
  generada al cargar el resumen (ADR-0005).

## Sesión e inactividad

- `app/InactivityTimer` reinicia un contador de 5 minutos con cada interacción y, al
  vencer, limpia el estado local y redirige a `/login` con un aviso. Es solo UX: la
  autoridad es el `401 session_expired` del servidor, que el `client.ts` intercepta y
  convierte en redirección (HU-04).
- Tras `logout`, la caché de TanStack Query se vacía para que "atrás" no muestre datos.

## Accesibilidad y responsive (RNF-03)

- Navegación completa por teclado; orden de tabulación lógico; foco visible; foco movido
  al título al cambiar de página.
- Todo control tiene etiqueta visible o `aria-label`. Imágenes decorativas con `alt=""`.
- Breakpoints: móvil primero (360 px), escritorio desde 1024 px. Sin scroll horizontal.
- Funciones principales (saldo, transferir, recargar, historial, perfil) accesibles desde
  la navegación principal en máximo tres clics desde el login (RNF-03.1).
- Playwright corre `@axe-core/playwright` en cada página principal; cualquier violación
  `serious` o `critical` falla el test.

## Pruebas unitarias con Ionic

Los componentes de Ionic son web components y **no se hidratan en jsdom**: `IonInput` no
crea el `<input>` interno, así que Testing Library no puede escribir en él. Por eso la
lógica de cada pantalla vive en un hook (`useRecharge`) que se prueba con `renderHook` y
MSW (validación, claves, errores, 401), y el componente de página solo se prueba por
render (títulos, textos, estados). La interacción real se cubre en Playwright.

## Pruebas E2E (Playwright)

- Un archivo por historia en `e2e/hu-NN-<slug>.spec.ts`, con al menos el camino exitoso
  y uno rechazado de sus criterios. Los escenarios citan el CA en el título:
  `test("HU-06 CA-5 rechaza transferencia a la propia cuenta", ...)`.
- Page objects en `e2e/pages/` con métodos de intención (`transferPage.prepare(phone,
  amount)`), selectores por rol y nombre accesible (`getByRole("button", { name:
  "Confirmar" })`), nunca por clase CSS ni `data-testid` salvo cuando no hay rol.
- Datos de prueba ficticios creados por API en `fixtures/` antes de cada test; nunca se
  dependen de datos preexistentes.
- Proyectos: `desktop-chromium` (1280×800) y `mobile-chromium` (Pixel 7). Los dos corren
  en CI.

```ts
// e2e/pages/transfer.page.ts
export class TransferPage {
  constructor(private readonly page: Page) {}
  async goto() { await this.page.goto("/transferir"); }
  async prepare(phone: string, amount: string) {
    await this.page.getByLabel("Teléfono del destinatario").fill(phone);
    await this.page.getByLabel("Monto (COP)").fill(amount);
    await this.page.getByRole("button", { name: "Revisar" }).click();
  }
  summary() { return this.page.getByRole("region", { name: "Resumen de la transferencia" }); }
  async confirm() { await this.page.getByRole("button", { name: "Confirmar" }).click(); }
}
```

## Dependencias

Misma política que la API: añadir una dependencia requiere ADR corto y commit propio
(`build(PPA-n): add <paquete>`), versiones exactas en `package.json` (`npm install
--save-exact`). Node 22 (`.nvmrc`). Lista inicial permitida: `react`, `react-dom`,
`@ionic/react`, `@ionic/react-router`, `ionicons`, `react-router-dom` 6,
`@tanstack/react-query`, `react-hook-form`; dev: `vite`,
`@vitejs/plugin-react`, `typescript` 5.x, `vitest`, `@vitest/coverage-v8`,
`@testing-library/react`, `@testing-library/user-event`, `@testing-library/jest-dom`,
`jsdom`, `msw` 2.x, `@playwright/test`, `@axe-core/playwright`, `openapi-typescript`,
`eslint` 9.x, `@eslint/js`, `typescript-eslint`, `eslint-plugin-react-hooks`,
`eslint-plugin-jsx-a11y`, `globals`, `prettier`, `@types/react`, `@types/react-dom`,
`@types/node`. ESLint se mantiene en 9 y TypeScript en 5 mientras `eslint-plugin-jsx-a11y`
y `typescript-eslint` no soporten las versiones mayores siguientes.

## Qué no hacer

- No guardar datos de sesión, teléfonos completos ni saldos en `localStorage`.
- No llamar a la API desde componentes: siempre a través de `features/<x>/api.ts` y
  `shared/api/client.ts`.
- No desactivar reglas de `jsx-a11y` con comentarios; se corrige el componente.
- No usar `window.alert`/`confirm`: los resultados y confirmaciones son componentes
  accesibles.
