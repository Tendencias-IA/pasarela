import {
  IonButtons,
  IonContent,
  IonHeader,
  IonMenuButton,
  IonPage,
  IonTitle,
  IonToolbar,
} from "@ionic/react";

/** Destino de los enlaces del menú cuya historia aún no está implementada. */
export function ComingSoonPage({ title, story }: { title: string; story: string }) {
  return (
    <IonPage>
      <IonHeader>
        <IonToolbar>
          <IonButtons slot="start">
            <IonMenuButton />
          </IonButtons>
          <IonTitle>{title}</IonTitle>
        </IonToolbar>
      </IonHeader>
      <IonContent className="ion-padding">
        <h1 className="tai-title">{title}</h1>
        <p role="status">Próximamente: esta pantalla llega con la historia {story}.</p>
      </IonContent>
    </IonPage>
  );
}
