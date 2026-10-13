// Exécuté par Vercel à chaque déploiement : génère config.js à partir des variables
// d'environnement Vercel (BACKEND_URL, AGENT_URL). Sans variables, config.js est conservé tel quel.
import { writeFileSync } from "node:fs";

const { BACKEND_URL, AGENT_URL } = process.env;
if (!BACKEND_URL) {
  console.log("BACKEND_URL absent : config.js du dépôt conservé.");
} else {
  const config = {
    BACKEND_URL,
    AGENT_URL: AGENT_URL || "https://apps.abacus.ai/chatllm/?appId=5b4213162",
  };
  writeFileSync("config.js",
    `// Généré automatiquement par build-config.mjs (variables Vercel).\nwindow.APP_CONFIG = ${JSON.stringify(config, null, 2)};\n`);
  console.log("config.js généré :", config);
}
