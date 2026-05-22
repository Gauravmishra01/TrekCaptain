import { API } from "../config/config.js";
import { httpPost } from "../utils/http.js";

export const AuthService = {
  sendLoginOtp(email) {
    return httpPost(API.BASE_URL + API.AUTH.LOGIN_EMAIL, { email });
  },

  verifyLoginOtp({ email, otpCode, verificationToken }) {
    return httpPost(API.BASE_URL + API.AUTH.VERIFY_OTP, {
      email,
      otpCode,
      verificationToken,
    });
  },
};
