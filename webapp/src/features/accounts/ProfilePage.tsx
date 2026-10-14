import {
  IonButton,
  IonButtons,
  IonContent,
  IonHeader,
  IonInput,
  IonItem,
  IonList,
  IonMenuButton,
  IonPage,
  IonTitle,
  IonToolbar,
} from "@ionic/react";
import { useEffect, useRef, useState } from "react";
import { Controller, useForm } from "react-hook-form";

import { ApiError } from "../../shared/api/client";
import { EmailEditor } from "./EmailEditor";
import { useProfile } from "./useProfile";

/** PPA-12 / HU-12: editar solo el teléfono de la cuenta autenticada. */
export function ProfilePage() {
  const { profile, changePhone, changeEmail } = useProfile();
  const [editing, setEditing] = useState(false);
  const title = useRef<HTMLHeadingElement>(null);
  const submitting = useRef(false);
  const {
    control,
    handleSubmit,
    reset,
    setError,
    formState: { errors },
  } = useForm<{ phone: string }>({
    defaultValues: { phone: "" },
    mode: "onTouched",
  });
  useEffect(() => {
    title.current?.focus();
  }, []);
  const save = async ({ phone }: { phone: string }) => {
    if (submitting.current) return;
    submitting.current = true;
    try {
      await changePhone.mutateAsync(phone);
      setEditing(false);
    } catch (error) {
      const message =
        error instanceof ApiError && error.code === "duplicate_identity"
          ? "Este teléfono ya está registrado."
          : error instanceof ApiError
            ? error.messagesByField().phone
            : undefined;
      setError("phone", { message: message ?? "No se pudo guardar. Intenta de nuevo." });
    } finally {
      submitting.current = false;
    }
  };
  const data = profile.data;
  return (
    <IonPage>
      <IonHeader>
        <IonToolbar>
          <IonButtons slot="start">
            <IonMenuButton />
          </IonButtons>
          <IonTitle>Mi perfil</IonTitle>
        </IonToolbar>
      </IonHeader>
      <IonContent className="ion-padding">
        <section
          className="tai-card"
          style={{ maxWidth: 640, margin: "0 auto" }}
          aria-labelledby="profile-title"
        >
          <h1 id="profile-title" ref={title} tabIndex={-1}>
            Mi perfil
          </h1>
          {profile.isPending && <p role="status">Cargando perfil…</p>}
          {profile.isError && (
            <p role="alert">
              {profile.error instanceof ApiError && profile.error.status === 401
                ? "Inicia sesión para consultar tu perfil."
                : "No se pudo cargar el perfil."}
            </p>
          )}
          {profile.isError && <IonButton routerLink="/login">Iniciar sesión</IonButton>}
          {data && (
            <>
              <IonList lines="full">
                <IonItem>
                  <IonInput
                    label="Nombre completo"
                    labelPlacement="stacked"
                    value={data.full_name ?? "Sin registrar"}
                    readonly
                  />
                </IonItem>
                <IonItem>
                  <IonInput
                    label="Número de identificación"
                    labelPlacement="stacked"
                    value={data.national_id ?? "Sin registrar"}
                    readonly
                  />
                </IonItem>
                <IonItem>
                  <IonInput
                    label="Correo electrónico"
                    labelPlacement="stacked"
                    value={data.email ?? "Sin registrar"}
                    readonly
                  />
                </IonItem>
              </IonList>
              <EmailEditor
                email={data.email}
                mutation={changeEmail}
                disabled={editing || changePhone.isPending}
              />
              {!editing ? (
                <>
                  <p>
                    Teléfono actual: <span>{data.phone}</span>
                  </p>
                  <IonButton
                    disabled={changeEmail.isPending}
                    onClick={() => {
                      reset({ phone: data.phone });
                      changePhone.reset();
                      setEditing(true);
                    }}
                  >
                    Editar teléfono
                  </IonButton>
                </>
              ) : (
                <form
                  noValidate
                  onSubmit={(event) => {
                    void handleSubmit(save)(event);
                  }}
                  aria-label="Cambiar teléfono"
                >
                  <Controller
                    name="phone"
                    control={control}
                    rules={{
                      required: "Ingresa el nuevo teléfono.",
                      pattern: {
                        value: /^3[0-9]{9}$/,
                        message: "Usa 10 dígitos, empezando por 3.",
                      },
                    }}
                    render={({ field }) => (
                      <IonInput
                        label="Nuevo teléfono"
                        labelPlacement="stacked"
                        type="tel"
                        inputmode="numeric"
                        autocomplete="tel"
                        required
                        aria-required="true"
                        value={field.value}
                        disabled={changePhone.isPending}
                        onIonInput={(event) => {
                          field.onChange(event.detail.value ?? "");
                        }}
                        onIonBlur={field.onBlur}
                        errorText={errors.phone?.message}
                        className={errors.phone ? "ion-invalid ion-touched" : ""}
                      />
                    )}
                  />
                  <IonButton type="submit" disabled={changePhone.isPending}>
                    {changePhone.isPending ? "Guardando…" : "Guardar teléfono"}
                  </IonButton>
                  <IonButton
                    fill="outline"
                    disabled={changePhone.isPending}
                    onClick={() => {
                      reset();
                      setEditing(false);
                      changePhone.reset();
                    }}
                  >
                    Cancelar
                  </IonButton>
                </form>
              )}
              {changePhone.isSuccess && (
                <p role="status">Teléfono actualizado. Usa el nuevo número para iniciar sesión.</p>
              )}
            </>
          )}
        </section>
      </IonContent>
    </IonPage>
  );
}
