// Storefront account service. Deployed behind the company load balancer at https://shop.example.com.
// Partner sites embed the notifications widget, which is why widget_session is SameSite=None.
const path = require("path");
const http = require("http");
const express = require("express");
const session = require("express-session");
const cookie = require("cookie");
const cors = require("cors");
const multer = require("multer");
const { WebSocketServer } = require("ws");
const db = require("./db");
const { csrfCheck } = require("./csrf"); // validates req.body._csrf against req.session.csrfToken

const app = express();
app.set("trust proxy", 1);
app.use(express.json());
app.use(express.urlencoded({ extended: false }));
app.use(
  session({
    name: "sid",
    secret: process.env.SESSION_SECRET,
    resave: false,
    saveUninitialized: false,
    cookie: { httpOnly: true, secure: true, sameSite: "lax" },
  }),
);

function requireLogin(req, res, next) {
  if (!req.session.userId) return res.status(401).json({ error: "login required" });
  next();
}

// ---- Public catalogue, consumed by partner sites from the browser ----
const catalog = express.Router();
catalog.use(cors({ origin: "*" })); // Access-Control-Allow-Origin: *, no credentials option
catalog.get("/products", async (req, res) => res.json(await db.products.listPublic()));
catalog.get("/me/recommendations", requireLogin, async (req, res) =>
  res.json(await db.recommendations.forUser(req.session.userId)),
);
app.use("/api/catalog", catalog);

// ---- Account settings ----
app.get("/account/email/change", requireLogin, async (req, res) => {
  // Link target used by the "update your email" banner.
  await db.users.update(req.session.userId, { email: String(req.query.email) });
  res.redirect("/account?changed=1");
});

app.post("/account/delete", requireLogin, csrfCheck, async (req, res) => {
  await db.users.softDelete(req.session.userId);
  req.session.destroy(() => res.redirect("/"));
});

// ---- Avatars ----
const upload = multer({
  dest: path.join(__dirname, "uploads"),
  limits: { fileSize: 2 * 1024 * 1024 },
  fileFilter: (req, file, cb) => cb(null, /\.(png|jpe?g|gif|svg)$/i.test(file.originalname)),
});

app.post("/account/avatar", requireLogin, upload.single("avatar"), csrfCheck, async (req, res) => {
  await db.users.update(req.session.userId, {
    avatarFile: req.file.filename, // multer's random name, no extension
    avatarType: req.file.mimetype, // as sent by the browser
  });
  res.redirect("/account");
});

app.get("/avatars/:userId", async (req, res) => {
  const user = await db.users.get(req.params.userId);
  if (!user || !user.avatarFile) return res.sendStatus(404);
  res.type(user.avatarType);
  res.sendFile(path.join(__dirname, "uploads", user.avatarFile));
});

// ---- Gift cards ----
app.post("/giftcards/redeem", requireLogin, csrfCheck, async (req, res) => {
  const card = await db.giftcards.findByCode(String(req.body.code));
  if (!card || card.redeemed_by) return res.status(400).json({ error: "invalid or used" });
  const claimed = await db.query(
    "UPDATE giftcards SET redeemed_by = $1, redeemed_at = now() WHERE id = $2 AND redeemed_by IS NULL",
    [req.session.userId, card.id],
  );
  if (claimed.rowCount !== 1) return res.status(409).json({ error: "already redeemed" });
  await db.query("UPDATE accounts SET balance_cents = balance_cents + $1 WHERE user_id = $2", [
    card.amount_cents,
    req.session.userId,
  ]);
  res.json({ ok: true });
});

// ---- Notifications widget (embedded on partner sites) ----
app.post("/widget/login", requireLogin, csrfCheck, async (req, res) => {
  const token = await db.widgetSessions.create(req.session.userId);
  res.cookie("widget_session", token, { httpOnly: true, secure: true, sameSite: "none" });
  res.sendStatus(204);
});

const server = http.createServer(app);
const wss = new WebSocketServer({ noServer: true });

server.on("upgrade", async (req, socket, head) => {
  if (new URL(req.url, "https://shop.example.com").pathname !== "/ws/notifications") {
    return socket.destroy();
  }
  const { widget_session: token } = cookie.parse(req.headers.cookie || "");
  const userId = token && (await db.widgetSessions.userFor(token));
  if (!userId) return socket.destroy();
  wss.handleUpgrade(req, socket, head, (ws) => {
    ws.userId = userId;
    db.notifications.subscribe(userId, (msg) => ws.send(JSON.stringify(msg))); // order updates, addresses
    ws.on("message", async (raw) => {
      const { action, id } = JSON.parse(raw);
      if (action === "dismiss") await db.notifications.dismiss(userId, id);
    });
  });
});

server.listen(3000);
