import {
  IonButton,
  IonContent,
  IonHeader,
  IonInput,
  IonItem,
  IonList,
  IonPage,
  IonRouterLink,
  IonTitle,
  IonToast,
  IonToolbar,
} from "@ionic/react";
import { useMutation } from "@tanstack/react-query";
import { alertCircle, checkmarkCircle } from "ionicons/icons";
import { useEffect, useRef, type FormEvent } from "react";
import { Controller, useForm } from "react-hook-form";

import { ApiError } from "../../shared/api/client";
import { registerAccount, type RegisterAccountInput } from "./api";

export function RegisterPage() {
  const titleRef = useRef<HTMLHeadingElement>(null);
  const submittingRef = useRef(false);
  useEffect(() => {
    titleRef.current?.focus();
  }, []);

  const {
    control,
    handleSubmit,
    setError,
    formState: { errors },
  } = useForm<RegisterAccountInput>({
    defaultValues: { full_name: "", phone: "", national_id: "", email: "", password: "" },
    mode: "onTouched",
    reValidateMode: "onChange",
  });
  const mutation = useMutation({
    mutationFn: registerAccount,
    onError(error) {
      if (error instanceof ApiError) {
        Object.entries(error.messagesByField()).forEach(([field, message]) => {
          setError(field as keyof RegisterAccountInput, { message });
        });
      }
    },
    onSettled() {
      submittingRef.current = false;
    },
  });
  const onSubmit = (event: FormEvent<HTMLFormElement>) => {
    void handleSubmit((data) => {
      if (submittingRef.current) return;
      submittingRef.current = true;
      mutation.mutate(data);
    })(event);
  };

  return (
    <IonPage>
      <IonHeader>
        <IonToolbar className="register-system-toolbar">
          <IonTitle>Moneo — Crear cuenta</IonTitle>
        </IonToolbar>
      </IonHeader>
      <IonContent fullscreen className="register-content">
        <main className="register-layout">
          <aside className="register-brand" aria-label="Moneo">
            <span className="register-orbit register-orbit-large" aria-hidden="true" />
            <span className="register-orbit register-orbit-small" aria-hidden="true" />
            <div className="register-brand-copy">
              <p className="register-logo">Moneo</p>
              <p className="register-promise">
                Crea tu cuenta y tu billetera queda lista con saldo inicial de $0 COP.
              </p>
            </div>
            <p className="register-disclaimer">Prototipo académico — dinero y datos ficticios.</p>
          </aside>

          <section className="register-form-panel" aria-labelledby="register-title">
            <div className="register-form-container">
              <header className="register-intro">
                <h1 id="register-title" tabIndex={-1} ref={titleRef}>
                  Crea tu cuenta
                </h1>
                <p>Completa tus datos para abrir tu billetera digital.</p>
              </header>
              <form onSubmit={onSubmit} noValidate>
                <IonList lines="none" className="register-fields">
                  <IonItem lines="none" className="register-field">
                    <Controller
                      name="full_name"
                      control={control}
                      rules={{
                        required: "El nombre es obligatorio.",
                        minLength: { value: 2, message: "Ingresa al menos 2 caracteres." },
                        maxLength: { value: 100, message: "Usa máximo 100 caracteres." },
                        pattern: {
                          value: /^[\p{L}\p{M}][\p{L}\p{M} '-]*[\p{L}\p{M}]$/u,
                          message: "Usa solo letras, espacios, apóstrofos o guiones.",
                        },
                      }}
                      render={({ field }) => (
                        <IonInput
                          label="Nombre completo"
                          aria-label="Nombre completo"
                          labelPlacement="stacked"
                          autocomplete="name"
                          placeholder="Laura Gómez"
                          required
                          value={field.value}
                          onInput={(event) => {
                            field.onChange(event.currentTarget.value ?? "");
                          }}
                          onIonBlur={field.onBlur}
                          errorText={errors.full_name?.message}
                          className={`register-input ${
                            errors.full_name ? "ion-invalid ion-touched" : ""
                          }`}
                        />
                      )}
                    />
                  </IonItem>
                  <div className="register-grid">
                    <IonItem lines="none" className="register-field">
                      <Controller
                        name="phone"
                        control={control}
                        rules={{
                          required: "El teléfono es obligatorio.",
                          pattern: {
                            value: /^3[0-9]{9}$/,
                            message: "Ingresa 10 dígitos comenzando por 3.",
                          },
                        }}
                        render={({ field }) => (
                          <IonInput
                            label="Número de teléfono"
                            aria-label="Número de teléfono"
                            labelPlacement="stacked"
                            inputmode="numeric"
                            autocomplete="tel"
                            placeholder="3001234567"
                            required
                            value={field.value}
                            onInput={(event) => {
                              field.onChange(event.currentTarget.value ?? "");
                            }}
                            onIonBlur={field.onBlur}
                            errorText={errors.phone?.message}
                            className={`register-input ${
                              errors.phone ? "ion-invalid ion-touched" : ""
                            }`}
                          />
                        )}
                      />
                    </IonItem>
                    <IonItem lines="none" className="register-field">
                      <Controller
                        name="national_id"
                        control={control}
                        rules={{
                          required: "La identificación es obligatoria.",
                          pattern: {
                            value: /^[A-Za-z0-9]{5,20}$/,
                            message: "Usa de 5 a 20 letras o números.",
                          },
                        }}
                        render={({ field }) => (
                          <IonInput
                            label="Número de identificación"
                            aria-label="Número de identificación"
                            labelPlacement="stacked"
                            autocomplete="off"
                            placeholder="1012345678"
                            required
                            value={field.value}
                            onInput={(event) => {
                              field.onChange(event.currentTarget.value ?? "");
                            }}
                            onIonBlur={field.onBlur}
                            errorText={errors.national_id?.message}
                            className={`register-input ${
                              errors.national_id ? "ion-invalid ion-touched" : ""
                            }`}
                          />
                        )}
                      />
                    </IonItem>
                  </div>
                  <IonItem lines="none" className="register-field">
                    <Controller
                      name="email"
                      control={control}
                      rules={{
                        required: "El correo es obligatorio.",
                        pattern: {
                          value: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
                          message: "Ingresa un correo válido.",
                        },
                      }}
                      render={({ field }) => (
                        <IonInput
                          label="Correo electrónico"
                          aria-label="Correo electrónico"
                          labelPlacement="stacked"
                          type="email"
                          autocomplete="email"
                          placeholder="laura@correo.com"
                          required
                          value={field.value}
                          onInput={(event) => {
                            field.onChange(event.currentTarget.value ?? "");
                          }}
                          onIonBlur={field.onBlur}
                          errorText={errors.email?.message}
                          className={`register-input ${
                            errors.email ? "ion-invalid ion-touched" : ""
                          }`}
                        />
                      )}
                    />
                  </IonItem>
                  <IonItem lines="none" className="register-field">
                    <Controller
                      name="password"
                      control={control}
                      rules={{
                        required: "La contraseña es obligatoria.",
                        minLength: { value: 8, message: "Usa al menos 8 caracteres." },
                        validate: (value) =>
                          (/\p{L}/u.test(value) && /[0-9]/.test(value)) ||
                          "Incluye al menos una letra y un número.",
                      }}
                      render={({ field }) => (
                        <IonInput
                          label="Contraseña"
                          aria-label="Contraseña"
                          labelPlacement="stacked"
                          type="password"
                          autocomplete="new-password"
                          placeholder="••••••••"
                          helperText="Mínimo 8 caracteres, con al menos una letra y un número."
                          required
                          value={field.value}
                          onInput={(event) => {
                            field.onChange(event.currentTarget.value ?? "");
                          }}
                          onIonBlur={field.onBlur}
                          errorText={errors.password?.message}
                          className={`register-input ${
                            errors.password ? "ion-invalid ion-touched" : ""
                          }`}
                        />
                      )}
                    />
                  </IonItem>
                </IonList>
                <IonButton
                  type="submit"
                  expand="block"
                  className="register-submit"
                  disabled={mutation.isPending}
                  aria-label="Crear cuenta"
                >
                  {mutation.isPending ? "Creando cuenta…" : "Crear cuenta"}
                </IonButton>
              </form>
              <p className="register-login-prompt">
                ¿Ya tienes cuenta? <IonRouterLink routerLink="/login">Inicia sesión</IonRouterLink>
              </p>
            </div>
            <IonToast
              isOpen={mutation.isSuccess}
              color="success"
              icon={checkmarkCircle}
              message="Tu cuenta y billetera fueron creadas. Tu saldo inicial es $0 COP."
              position="top"
              buttons={[{ text: "Cerrar", role: "cancel" }]}
              htmlAttributes={{
                role: "status",
                "aria-live": "polite",
                "aria-label": "Tu cuenta y billetera fueron creadas. Tu saldo inicial es $0 COP.",
              }}
              onDidDismiss={() => {
                mutation.reset();
              }}
            />
            <IonToast
              isOpen={
                mutation.isError &&
                Object.keys(
                  mutation.error instanceof ApiError ? mutation.error.messagesByField() : {},
                ).length === 0
              }
              color="danger"
              icon={alertCircle}
              message={mutation.error?.message}
              position="top"
              buttons={[{ text: "Cerrar", role: "cancel" }]}
              htmlAttributes={{
                role: "alert",
                "aria-live": "assertive",
                "aria-label": mutation.error?.message,
              }}
              onDidDismiss={() => {
                mutation.reset();
              }}
            />
          </section>
        </main>
      </IonContent>
    </IonPage>
  );
}
