import path from "path";
import process from "process";
import { fileURLToPath } from "url";
import express from "express";
import cors from "cors";
import dotenv from "dotenv";
import jwt from "jsonwebtoken";
import { spawn } from "child_process";
import crypto from "crypto";

dotenv.config();

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..");

const app = express();
app.use(cors());
app.use(express.json({ limit: "1mb" }));

const PORT = process.env.PORT || 4000;
const BOT_SHARED_SECRET = process.env.BOT_SHARED_SECRET || "";
const JWT_SECRET = process.env.JWT_SECRET || "dev-secret";
const PYTHON_BIN = process.env.PYTHON_BIN || "python3";
const RAG_RUNNER = process.env.RAG_RUNNER || path.join(repoRoot, "backend", "scripts", "rag_runner.py");
const utcDateKey = (date = new Date()) => {
  const year = date.getUTCFullYear();
  const month = String(date.getUTCMonth() + 1).padStart(2, "0");
  const day = String(date.getUTCDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
};

const nextUtcMidnight = (date = new Date()) => {
  const next = new Date(Date.UTC(date.getUTCFullYear(), date.getUTCMonth(), date.getUTCDate() + 1, 0, 0, 0));
  return next;
};

const normalizeCode = (value) => String(value || "").trim().replace(/\s+/g, "");

const dailyCode = (telegramUserId, dayKey, length = 6) => {
  const secret = BOT_SHARED_SECRET;
  if (!secret) return null;
  const hmac = crypto.createHmac("sha256", secret);
  hmac.update(`${telegramUserId}:${dayKey}`);
  const hex = hmac.digest("hex");
  const digits = hex.replace(/[^0-9]/g, "");
  const padded = (digits + "000000000000").slice(0, length);
  return padded;
};

const issueToken = (telegramUserId) => {
  const now = new Date();
  const expDate = nextUtcMidnight(now);
  const payload = {
    sub: String(telegramUserId),
    day: utcDateKey(now),
  };
  return jwt.sign(payload, JWT_SECRET, { expiresIn: Math.floor((expDate.getTime() - now.getTime()) / 1000) });
};

const requireAuth = (req, res, next) => {
  const header = req.headers.authorization || "";
  const token = header.startsWith("Bearer ") ? header.slice(7) : null;
  if (!token) {
    return res.status(401).json({ error: "missing_token" });
  }
  try {
    req.user = jwt.verify(token, JWT_SECRET);
    return next();
  } catch (err) {
    return res.status(401).json({ error: "invalid_token" });
  }
};

app.get("/health", (_req, res) => {
  res.json({ ok: true });
});

// Frontend verifies user code and receives a 1-day token.
app.post("/auth/verify", (req, res) => {
  const { telegramUserId, code } = req.body || {};
  if (!telegramUserId || !code) {
    return res.status(400).json({ error: "missing_fields" });
  }
  const dayKey = utcDateKey();
  const expected = dailyCode(telegramUserId, dayKey);
  if (!expected) {
    return res.status(500).json({ error: "missing_bot_secret" });
  }
  if (normalizeCode(code) !== expected) {
    return res.status(401).json({ error: "invalid_code" });
  }
  const token = issueToken(telegramUserId);
  return res.json({ token, expiresAtUtc: nextUtcMidnight().toISOString() });
});

app.post("/chat", requireAuth, (req, res) => {
  const { prompt } = req.body || {};
  if (!prompt || typeof prompt !== "string") {
    return res.status(400).json({ error: "missing_prompt" });
  }

  const payload = JSON.stringify({ prompt: prompt.trim() });
  const child = spawn(PYTHON_BIN, [RAG_RUNNER], {
    cwd: repoRoot,
    env: { ...process.env, PYTHONPATH: repoRoot },
  });

  let stdout = "";
  let stderr = "";

  child.stdout.on("data", (chunk) => {
    stdout += chunk.toString();
  });
  child.stderr.on("data", (chunk) => {
    stderr += chunk.toString();
  });

  child.on("close", (code) => {
    if (code !== 0) {
      return res.status(500).json({ error: "rag_failed", details: stderr.trim() });
    }
    try {
      const parsed = JSON.parse(stdout);
      return res.json(parsed);
    } catch (err) {
      return res.status(500).json({ error: "bad_rag_response", details: stderr.trim() });
    }
  });

  child.stdin.write(payload);
  child.stdin.end();
});

app.listen(PORT, () => {
  console.log(`Backend listening on ${PORT}`);
});
