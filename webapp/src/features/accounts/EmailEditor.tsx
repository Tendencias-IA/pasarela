import { IonButton, IonInput } from "@ionic/react";
import { useRef, useState } from "react";
import { Controller, useForm } from "react-hook-form";

import { ApiError } from "../../shared/api/client";
import type { useProfile } from "./useProfile";

interface Props {
  email: string | null;
  mutation: ReturnType<typeof useProfile>["changeEmail"];
  disabled: boolean;
}

/** HU-13: editar y cancelar únicamente el correo, sin verificaciones externas. */
export function EmailEditor({ email, mutation, disabled }: Props) {
  const [editing, setEditing] = useState(false);
  const sending = useRef(false);
  const {
    control,
    reset,
    handleSubmit,
    setError,
    formState: { errors },
  } = useForm<{ email: string }>({ defaultValues: { email: "" }, mode: "onTouched" });
  const save = async ({ email: value }: { email: string }) => {
    if (sending.current) return;
    sending.current = true;
    try {
      await mutation.mutateAsync(value.trim());
      setEditing(false);
    } catch (error) {
      const message =
        error instanceof ApiError && error.code === "duplicate_identity"
          ? "Este correo ya está registrado."
          : error instanceof ApiError
            ? error.messagesByField().email
            : undefined;
      setError("email", { message: message ?? "No se pudo guardar. Intenta de nuevo." });
    } finally {
      sending.current = false;
    }
  };
  return (
    <section aria-label="Editar correo electrónico">
      {!editing ? (
        <>
          <p>
            Correo actual: <span>{email ?? "Sin registrar"}</span>
          </p>
          <IonButton
            disabled={disabled}
            onClick={() => {
              reset({ email: email ?? "" });
              mutation.reset();
              setEditing(true);
            }}
          >
            Editar correo
          </IonButton>
        </>
      ) : (
        <form
          noValidate
          aria-label="Cambiar correo"
          onSubmit={(event) => {
            void handleSubmit(save)(event);
          }}
        >
          <Controller
            name="email"
            control={control}
            rules={{
              required: "Ingresa el nuevo correo.",
              validate: (value) =>
                (value.trim().length <= 254 && /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value.trim())) ||
                "Ingresa un correo válido.",
            }}
            render={({ field }) => (
              <IonInput
                label="Nuevo correo"
                labelPlacement="stacked"
                type="email"
                inputmode="email"
                autocomplete="email"
                required
                aria-required="true"
                value={field.value}
                disabled={mutation.isPending || disabled}
                onIonInput={(event) => {
                  field.onChange(event.detail.value ?? "");
                }}
                onIonBlur={field.onBlur}
                errorText={errors.email?.message}
                className={errors.email ? "ion-invalid ion-touched" : ""}
              />
            )}
          />
          <IonButton type="submit" disabled={mutation.isPending || disabled}>
            {mutation.isPending ? "Guardando…" : "Guardar correo"}
          </IonButton>
          <IonButton
            fill="outline"
            disabled={mutation.isPending}
            onClick={() => {
              reset();
              setEditing(false);
              mutation.reset();
            }}
          >
            Cancelar correo
          </IonButton>
        </form>
      )}
      {mutation.isSuccess && <p role="status">Correo actualizado.</p>}
    </section>
  );
}
