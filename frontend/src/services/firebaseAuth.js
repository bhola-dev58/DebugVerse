/**
 * Firebase Authentication Service for DebugVerse
 * Supports Google, GitHub, Facebook, Phone (SMS OTP), and Email/Password
 */

import {
  auth,
  googleProvider,
  githubProvider,
  facebookProvider,
  signInWithPopup,
  signInWithPhoneNumber,
  RecaptchaVerifier,
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword,
  updateProfile,
  signOut,
} from "../config/firebase";

/**
 * 1. Social Provider Sign In (Google, GitHub, Facebook)
 */
export const signInWithSocialProvider = async (providerName) => {
  let provider;
  switch (providerName) {
    case "google":
      provider = googleProvider;
      break;
    case "github":
      provider = githubProvider;
      break;
    case "facebook":
      provider = facebookProvider;
      break;
    default:
      throw new Error(`Unsupported provider: ${providerName}`);
  }

  const result = await signInWithPopup(auth, provider);
  const token = await result.user.getIdToken();
  return { user: result.user, token };
};

/**
 * 2. Setup Invisible Recaptcha for Phone Verification
 */
export const initPhoneRecaptcha = (containerId = "recaptcha-container") => {
  if (typeof window === "undefined") return null;

  if (window.recaptchaVerifier) {
    try {
      window.recaptchaVerifier.clear();
    } catch {
      // Ignore if already cleared
    }
  }

  window.recaptchaVerifier = new RecaptchaVerifier(
    auth,
    containerId,
    {
      size: "invisible",
      callback: () => {
        // reCAPTCHA solved
      },
      "expired-callback": () => {
        if (window.recaptchaVerifier) {
          window.recaptchaVerifier.clear();
        }
      },
    }
  );

  return window.recaptchaVerifier;
};

/**
 * 3. Send SMS Verification Code
 * @param {string} phoneNumber E.164 formatted phone number (e.g. +16505553434, +919876543210)
 */
export const sendPhoneVerificationCode = async (phoneNumber) => {
  const verifier = initPhoneRecaptcha("recaptcha-container");
  const confirmationResult = await signInWithPhoneNumber(auth, phoneNumber, verifier);
  window.phoneConfirmationResult = confirmationResult;
  return confirmationResult;
};

/**
 * 4. Verify SMS OTP Code
 * @param {string} otp 6-digit verification code
 */
export const confirmPhoneOtp = async (otp) => {
  if (!window.phoneConfirmationResult) {
    throw new Error("No pending verification. Please request a new SMS code.");
  }
  const result = await window.phoneConfirmationResult.confirm(otp);
  const token = await result.user.getIdToken();
  return { user: result.user, token };
};

/**
 * 5. Email/Password Authentication
 */
export const loginWithEmailPassword = async (email, password) => {
  const result = await signInWithEmailAndPassword(auth, email, password);
  const token = await result.user.getIdToken();
  return { user: result.user, token };
};

export const signupWithEmailPassword = async (email, password, displayName = "") => {
  const result = await createUserWithEmailAndPassword(auth, email, password);
  if (displayName && result.user) {
    await updateProfile(result.user, { displayName });
  }
  const token = await result.user.getIdToken();
  return { user: result.user, token };
};

/**
 * 6. Sign Out
 */
export const logoutFromFirebase = async () => {
  await signOut(auth);
};
