const apiBaseUrl = (
  import.meta.env.VITE_API_URL ?? "http://localhost:8000"
).replace(/\/$/, "");

// API configuration
export const API = {
  BASE_URL: `${apiBaseUrl}/api/v1`,

  AUTH: {
    LOGIN_EMAIL: "/agencies/login-email",
    VERIFY_OTP: "/agencies/verify-email-otp",
  },
};
