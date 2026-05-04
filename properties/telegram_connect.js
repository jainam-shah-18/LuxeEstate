/**
 * LuxeEstate — Telegram Connect Button
 * =====================================
 * Drop this <script> block at the bottom of the template that contains
 * your existing chatbot widget (e.g. base.html or chatbot.html).
 *
 * It injects a "Connect with Telegram" button inside the chatbot header.
 * When clicked, it opens your Telegram bot in a new tab.
 *
 * CONFIGURATION:
 *   Set window.LUXE_TELEGRAM_BOT_USERNAME to your bot's username.
 *   (the part after t.me/). You can do this inline:
 *
 *     <script>window.LUXE_TELEGRAM_BOT_USERNAME = "LuxeEstateBot";</script>
 *
 *   Or from Django template context:
 *     <script>window.LUXE_TELEGRAM_BOT_USERNAME = "{{ TELEGRAM_BOT_USERNAME }}";</script>
 */

function injectButton() {
  const header = document.querySelector(".luxe-chat-header");

  if (!header) {
    console.log("Telegram button: header not found");
    return;
  }

  // Prevent duplicate buttons
  if (document.getElementById("luxe-telegram-btn")) return;

  const btn = document.createElement("a");

  btn.id = "luxe-telegram-btn";
  btn.href = TELEGRAM_URL;
  btn.target = "_blank";
  btn.rel = "noopener noreferrer";

  btn.innerHTML = `
    <i class="fab fa-telegram-plane"></i>
    <span>Telegram</span>
  `;

  Object.assign(btn.style, {
    display: "inline-flex",
    alignItems: "center",
    gap: "6px",
    padding: "8px 14px",
    borderRadius: "999px",
    background: "#229ED9",
    color: "#fff",
    fontSize: "13px",
    fontWeight: "600",
    textDecoration: "none",
    marginLeft: "12px",
    transition: "0.3s ease",
    boxShadow: "0 6px 18px rgba(34,158,217,0.3)",
  });

  btn.addEventListener("mouseenter", () => {
    btn.style.transform = "translateY(-2px)";
  });

  btn.addEventListener("mouseleave", () => {
    btn.style.transform = "translateY(0)";
  });

  header.appendChild(btn);

  console.log("Telegram button injected successfully");
}