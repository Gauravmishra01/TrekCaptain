export const emailPattern = {
  value: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
  message: "Invalid email address",
};

export const passwordRules = () => ({
  required: "Password is required",
  minLength: {
    value: 8,
    message: "Password must be at least 8 characters long",
  },
});

export const confirmPasswordRules = (getValues: any) => ({
  validate: (value: string) =>
    value === String(getValues("password") ?? "") ||
    "The passwords do not match",
});

export function handleError(error: unknown): string {
  const responseError = error as {
    response?: {
      data?: {
        detail?: string;
        message?: string;
      };
    };
    message?: string;
  };

  const message =
    responseError.response?.data?.detail ??
    responseError.response?.data?.message ??
    responseError.message ??
    (error instanceof Error ? error.message : "An unexpected error occurred");

  if (typeof window !== "undefined") {
    window.alert(message);
  }

  return message;
}
