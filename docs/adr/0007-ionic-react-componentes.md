# ADR-0007: Ionic React como librería de componentes de la webapp

**Estado**: Aceptada
**Fecha**: 2026-10-14
**Ticket**: PPA-26

## Contexto

RNF-03 exige una interfaz responsive para escritorio y móvil, navegable por teclado, con
etiquetas comprensibles y formularios que señalen campos obligatorios y errores. El
esqueleto de `webapp/` no fijaba ninguna librería de componentes: cada historia habría
tenido que construir botones, campos, listas y alertas a mano, con accesibilidad
desigual entre compañeros.

## Decisión

Se adopta **Ionic React** (`@ionic/react` 9) como librería de componentes por defecto,
con `@ionic/react-router` 9 y `react-router-dom` 6.4+ para la navegación (Ionic 9 exige
react-router 6 y no soporta la 7). `ionicons` para iconos. Toda pantalla se compone con `IonPage`, `IonHeader`,
`IonContent` y los componentes de Ionic (`IonInput`, `IonButton`, `IonList`, `IonAlert`,
`IonToast`, `IonInfiniteScroll`); `shared/ui/` queda solo para envoltorios finos que
añaden las convenciones del proyecto (por ejemplo, `MoneyInput` sobre `IonInput`).

## Alternativas consideradas

- **MUI (Material UI)**: madura y muy documentada, pero orientada a escritorio; el
  patrón móvil (navegación por páginas, listas, pull to refresh, teclado numérico) hay
  que construirlo. El equipo prefirió Ionic por la prioridad móvil de la billetera.
- **Componentes propios con CSS**: control total y sin dependencia, pero cada historia
  reinventaría accesibilidad y responsive, justo lo que RNF-03 obliga a garantizar.

## Consecuencias

- La navegación usa `react-router-dom` 6 (`Routes`/`Route`/`useNavigate`) dentro de
  `IonReactRouter` e `IonRouterOutlet`; no se actualiza a la 7 hasta que Ionic la soporte.
- Los componentes de Ionic usan web components con shadow DOM: en Vitest y Playwright se
  consulta por rol y texto del contenido (light DOM), y los `label` de `IonInput` se
  pasan por la propiedad `label`, no con `<label for>`.
- Tema y colores se definen en `src/theme/variables.css` con las variables de Ionic; no
  se añade otra librería de estilos.
