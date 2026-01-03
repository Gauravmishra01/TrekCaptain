import { AuthService } from '../services/auth.service.js';

export async function sendOtpController() {
    const emailInput = document.getElementById('loginEmail');
    const email = emailInput.value.trim();

    if (!email) {
        alert('Please enter email');
        return;
    }

    try {
        // Disable button (UX)
        const btn = event.target;
        btn.disabled = true;
        btn.innerText = 'Sending OTP...';

        const response = await AuthService.sendLoginOtp(email);

        console.log(response.message); // OTP sent

        document.getElementById('emailStep').classList.add('hidden');
        document.getElementById('otpStep').classList.remove('hidden');

        setupOtpInputs();

    } catch (error) {
        alert(error.message);
    } finally {
        btn.disabled = false;
        btn.innerText = 'Send OTP';
    }
}
