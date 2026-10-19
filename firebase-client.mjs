import { initializeApp } from "https://www.gstatic.com/firebasejs/10.7.1/firebase-app.js";
import { getAuth, signInAnonymously, setPersistence, browserLocalPersistence } from "https://www.gstatic.com/firebasejs/10.7.1/firebase-auth.js";
import { getDatabase } from "https://www.gstatic.com/firebasejs/10.7.1/firebase-database.js";
import { firebaseConfig } from "./firebase-config.js";
export { ref, set, get, update, remove, onValue, push, onDisconnect, runTransaction, serverTimestamp, query, orderByChild, limitToLast } from "https://www.gstatic.com/firebasejs/10.7.1/firebase-database.js";

export async function connectFirebase() {
  if (!firebaseConfig.apiKey || firebaseConfig.apiKey === "AIzaSyBsomething") {
    throw new Error("Doplň konfiguraci Firebase podle README a zapni anonymní přihlášení.");
  }
  const app = initializeApp(firebaseConfig);
  const auth = getAuth(app);
  await setPersistence(auth, browserLocalPersistence);
  await auth.authStateReady();
  const user = auth.currentUser || (await signInAnonymously(auth)).user;
  return { db: getDatabase(app), uid: user.uid };
}
