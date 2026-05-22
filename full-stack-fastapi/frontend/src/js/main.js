import {
  closeLoginModal,
  openLoginModal,
  sendOtpController,
  setupOtpInputs,
  verifyOtp,
} from "./controllers/auth.controller.js";

window.closeLoginModal = closeLoginModal;
window.openLoginModal = openLoginModal;
window.sendOtpController = sendOtpController;
window.setupOtpInputs = setupOtpInputs;
window.verifyOtp = verifyOtp;

setupOtpInputs();
