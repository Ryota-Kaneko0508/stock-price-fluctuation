import { initializeApp } from "firebase/app";
import { getAuth } from "firebase/auth";

const firebaseConfig = {
  apiKey: "AIzaSyANU9WdVdsB0DI6pUg6Ao_wjqCCcS9l3u0",
  authDomain: "stock-app-c58c5.firebaseapp.com",
  projectId: "stock-app-c58c5",
  storageBucket: "stock-app-c58c5.firebasestorage.app",
  messagingSenderId: "404985982279",
  appId: "1:404985982279:web:1a9f283f55a9fd896bf062"
};

const app = initializeApp(firebaseConfig);
const auth = getAuth(app);

export { auth };