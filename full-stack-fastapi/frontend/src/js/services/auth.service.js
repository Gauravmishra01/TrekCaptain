import { API } from '../config/api.config.js';
import { httpPost } from '../utils/http.js';

export const AuthService = {
    sendLoginOtp(email) {
        return httpPost(
            API.BASE_URL + API.AUTH.LOGIN_EMAIL,
            { email }
        );
    }
};
