import { AuthService } from "../services/auth.service.js";

const OTP_TOKEN_KEY = "trekcaptain_login_verification_token";
const OTP_EMAIL_KEY = "trekcaptain_login_email";

function getElement(id) {
  return document.getElementById(id);
}

function toggleHidden(element, hidden) {
  if (!element) {
    return;
  }
  element.classList.toggle("hidden", hidden);
}

function getOtpInputs() {
  return Array.from(document.querySelectorAll(".otp-input"));
}

function getOtpCode() {
  return getOtpInputs()
    .map((input) => input.value.trim())
    .join("");
}

export function setupOtpInputs() {
  const otpInputs = getOtpInputs();

  otpInputs.forEach((input, index) => {
    input.oninput = () => {
      input.value = input.value.slice(-1);
      if (input.value && otpInputs[index + 1]) {
        otpInputs[index + 1].focus();
      }
    };

    input.onkeydown = (event) => {
      if (event.key === "Backspace" && !input.value && otpInputs[index - 1]) {
        otpInputs[index - 1].focus();
      }
    };
  });
}

export function openLoginModal() {
  const modal = getElement("loginModal");
  if (!modal) {
    return;
  }

  modal.classList.remove("hidden");
  modal.classList.add("flex");
  document.body.style.overflow = "hidden";
}

export function closeLoginModal() {
  const modal = getElement("loginModal");
  if (!modal) {
    return;
  }

  modal.classList.add("hidden");
  modal.classList.remove("flex");
  document.body.style.overflow = "";
}

export async function sendOtpController(event) {
  const emailInput = getElement("loginEmail");
  const email = emailInput?.value.trim() ?? "";

  if (!email) {
    alert("Please enter email");
    return;
  }

  const sendButton = event?.currentTarget ?? null;
  const buttonLabel = sendButton?.innerText ?? "Send OTP";

  try {
    const response = await AuthService.sendLoginOtp(email);
    sessionStorage.setItem(OTP_TOKEN_KEY, response.verification_token);
    sessionStorage.setItem(OTP_EMAIL_KEY, email);

    toggleHidden(getElement("emailStep"), true);
    toggleHidden(getElement("otpStep"), false);

    setupOtpInputs();
    getOtpInputs()[0]?.focus();
  } catch (error) {
    alert(error instanceof Error ? error.message : "Failed to send OTP");
  } finally {
    if (sendButton) {
      sendButton.disabled = false;
      sendButton.innerText = buttonLabel;
    }
  }
}

export async function verifyOtp() {
  const email =
    sessionStorage.getItem(OTP_EMAIL_KEY) ??
    getElement("loginEmail")?.value.trim() ??
    "";
  const verificationToken = sessionStorage.getItem(OTP_TOKEN_KEY) ?? "";
  const otpCode = getOtpCode();

  if (otpCode.length !== 6) {
    alert("Please enter the 6-digit OTP");
    return;
  }

  if (!email || !verificationToken) {
    alert("Request a new OTP before verifying");
    return;
  }

  try {
    await AuthService.verifyLoginOtp({
      email,
      otpCode,
      verificationToken,
    });
    sessionStorage.removeItem(OTP_EMAIL_KEY);
    sessionStorage.removeItem(OTP_TOKEN_KEY);
    closeLoginModal();
    window.location.href = "/gowithDaddy_dashboard.html";
  } catch (error) {
    alert(error instanceof Error ? error.message : "OTP verification failed");
  }
}
